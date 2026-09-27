# 코드 발췌 · 공유 거리장과 단방향 낙하

[← 포트폴리오](../README.md) · [소스 출처](../SOURCE_MAP.md)

실제 커밋에서 가져온 읽기용 발췌입니다. include·선언·주변 초기화 등이 생략돼 독립 컴파일되지 않습니다. 테스트 발췌도 전체 fixture와 실행 결과를 포함하지 않습니다.

원본 파일의 고지: `// Copyright Epic Games, Inc. All Rights Reserved.`

## UFPSRFlowFieldComputer::RebuildDropLinks

원본: `Source/FPSRoguelite/Private/Enemy/FPSRFlowFieldComputer.cpp` · L215–L303

```cpp
void UFPSRFlowFieldComputer::RebuildDropLinks()
{
	const int32 NumCells = GridDimX * GridDimY;
	const int32 NumSurf = NumCells * NumLayers;
	DropTarget.Init(INDEX_NONE, NumSurf * 4);
	DropInStart.Init(0, NumSurf + 1);
	DropInSource.Reset();

	if (NumCells <= 0 || MaxDropHeight <= 0.0f || DropMask.Num() != NumSurf)
	{
		return; // drops off (this run's cap, or no drop data at all) — arrays stay correctly-sized-but-empty
	}

	// Same direction order as DropMask's own bit contract ({+X,-X,+Y,-Y}) and RunBFS's DX4/DY4.
	static const int32 DropDX[4] = { 1, -1, 0, 0 };
	static const int32 DropDY[4] = { 0, 0, 1, -1 };

	// Pass 1: resolve every surface's own active drop target(s) — pure array math (DropMask + the shared landing
	// helper + IsSurfaceEdgeTraversable + MaxDropHeight).
	TArray<int32> IncomingCount;
	IncomingCount.Init(0, NumSurf);
	for (int32 Cell = 0; Cell < NumCells; ++Cell)
	{
		const int32 CX = Cell % GridDimX;
		const int32 CY = Cell / GridDimX;
		for (int32 RA = 0; RA < NumLayers; ++RA)
		{
			const int32 SA = SurfIndex(Cell, RA);
			const float ZA = CellFloorZ[SA];
			if (ZA == MAX_flt || DropMask[SA] == 0)
			{
				continue;
			}
			for (int32 N = 0; N < 4; ++N)
			{
				if (!((DropMask[SA] >> N) & 1u))
				{
					continue;
				}
				const int32 NX = CX + DropDX[N];
				const int32 NY = CY + DropDY[N];
				if (NX < 0 || NX >= GridDimX || NY < 0 || NY >= GridDimY)
				{
					continue;
				}
				const int32 NCell = NY * GridDimX + NX;
				const int32 RB = FindDropLandingRank(CellFloorZ, NCell, ZA, ActiveClimbableStepHeight);
				if (RB == INDEX_NONE)
				{
					continue;
				}
				const int32 SB = SurfIndex(NCell, RB);
				if (IsSurfaceEdgeTraversable(Cell, RA, NCell, RB))
				{
					continue; // already reachable by a normal edge — a drop link here would be pure redundancy
				}
				const float ZB = CellFloorZ[SB];
				if (ZA - ZB > MaxDropHeight)
				{
					continue; // geometrically clear at bake time, but taller than THIS run's cap
				}
				DropTarget[SA * 4 + N] = SB;
				++IncomingCount[SB];
			}
		}
	}

	// Pass 2: CSR prefix sum + fill, so RunBFS can relax a landing surface's upstream drop sources in O(1) per
	// link when that surface is dequeued, instead of scanning every surface's DropMask each time.
	DropInStart[0] = 0;
	for (int32 S = 0; S < NumSurf; ++S)
	{
		DropInStart[S + 1] = DropInStart[S] + IncomingCount[S];
	}
	DropInSource.Init(INDEX_NONE, DropInStart[NumSurf]);
	TArray<int32> FillCursor = DropInStart;
	for (int32 SA = 0; SA < NumSurf; ++SA)
	{
		for (int32 N = 0; N < 4; ++N)
		{
			const int32 SB = DropTarget[SA * 4 + N];
			if (SB == INDEX_NONE)
			{
				continue;
			}
			DropInSource[FillCursor[SB]++] = SA;
		}
	}
}
```

## UFPSRFlowFieldComputer::RunBFS

원본: `Source/FPSRoguelite/Private/Enemy/FPSRFlowFieldComputer.cpp` · L464–L701

```cpp
void UFPSRFlowFieldComputer::RunBFS(const TArray<int32>& SourceSurfaces)
{
	if (GridDimX <= 0 || GridDimY <= 0)
	{
		bFieldReady = false;
		bConnectivityReady = false;
		ComponentLabels.Reset();
		return;
	}

	// Connectivity is topology-based (source-independent), so refresh it here -> it's valid whenever the field is queried
	// (the combat gate reads it right after the subsystem's post-mutation RunBFS, same freshness contract as the flow).
	RebuildConnectivity();
	bConnectivityReady = true; // labels valid now, INDEPENDENT of whether flow sources resolve below (Codex R15)

	const int32 NumSurf = GridDimX * GridDimY * NumLayers;
	for (int32 i = 0; i < NumSurf; ++i)
	{
		DistField[i] = MAX_int32;
	}

	// Seed BFS from the resolved source surfaces (multi-source -> field points to NEAREST source/player).
	TQueue<int32> Frontier;
	bool bAnySource = false;
	for (const int32 Surf : SourceSurfaces)
	{
		if (Surf != INDEX_NONE && DistField.IsValidIndex(Surf) && DistField[Surf] != 0)
		{
			DistField[Surf] = 0;
			Frontier.Enqueue(Surf);
			bAnySource = true;
		}
	}

	if (!bAnySource)
	{
		bFieldReady = false;
		return;
	}

	// 4-connected BFS (uniform cost) over the surface graph -> integration field.
	static const int32 DX4[4] = { 1, -1, 0, 0 };
	static const int32 DY4[4] = { 0, 0, 1, -1 };
	int32 Current;
	while (Frontier.Dequeue(Current))
	{
		const int32 CurDist = DistField[Current];
		const int32 Cell = Current / NumLayers;
		const int32 Rank = Current - Cell * NumLayers;
		const int32 CX = Cell % GridDimX;
		const int32 CY = Cell / GridDimX;
		for (int32 N = 0; N < 4; ++N)
		{
			const int32 NX = CX + DX4[N];
			const int32 NY = CY + DY4[N];
			if (NX < 0 || NX >= GridDimX || NY < 0 || NY >= GridDimY)
			{
				continue;
			}
			const int32 NCell = NY * GridDimX + NX;
			for (int32 RB = 0; RB < NumLayers; ++RB)
			{
				const int32 NSurf = SurfIndex(NCell, RB);
				if (CellFloorZ[NSurf] == MAX_flt || BlockedField[NSurf])
				{
					continue; // absent, or an occupancy-blocked wall surface — never propagate flow through it
				}
				if (!IsSurfaceEdgeTraversable(Cell, Rank, NCell, RB))
				{
					continue; // a thin wall / non-traversable height change on the shared boundary blocks this edge
				}
				if (DistField[NSurf] > CurDist + 1)
				{
					DistField[NSurf] = CurDist + 1;
					Frontier.Enqueue(NSurf);
				}
			}
		}

		// TOWER-PATH C4: relax every surface A with an ACTIVE one-way drop INTO Current — A can move A->Current
		// (a fall), so A's distance-to-source can be Current's distance + 1, even though the drop is not a normal
		// EdgeMask edge (IsSurfaceEdgeTraversable would reject it) and A may not be orthogonally reachable FROM
		// Current at all (a ledge you can fall off but never climb back up through the same link).
		if (DropInStart.Num() == NumSurf + 1)
		{
			for (int32 K = DropInStart[Current]; K < DropInStart[Current + 1]; ++K)
			{
				const int32 SourceA = DropInSource[K];
				if (CellFloorZ[SourceA] == MAX_flt || BlockedField[SourceA])
				{
					continue;
				}
				if (DistField[SourceA] > CurDist + 1)
				{
					DistField[SourceA] = CurDist + 1;
					Frontier.Enqueue(SourceA);
				}
			}
		}
	}

	// Flow per surface: steepest descent toward the lowest-distance reachable neighbour surface.
	static const int32 DX8[8] = { 1, -1, 0, 0, 1, 1, -1, -1 };
	static const int32 DY8[8] = { 0, 0, 1, -1, 1, -1, 1, -1 };
	// TOWER-PATH C5: a BLOCKED surface's escape heading must not point across too steep a rise/drop — without this
	// the loops below judge a blocked surface's neighbours purely by BFS distance, ignoring height entirely. Same
	// formula the bake itself uses to decide what counts as a traversable "ramp" (BuildFromTraceRequest), via the
	// one shared helper, so the two paths can never quietly disagree about what a given WalkableNormalZ allows.
	const float RuntimeRampAllowance = ActiveCellSize * ComputeMaxSlopeTan(WalkableNormalZ);
	for (int32 CY = 0; CY < GridDimY; ++CY)
	{
		for (int32 CX = 0; CX < GridDimX; ++CX)
		{
			const int32 Cell = CY * GridDimX + CX;
			for (int32 Rank = 0; Rank < NumLayers; ++Rank)
			{
				const int32 Surf = SurfIndex(Cell, Rank);
				if (CellFloorZ[Surf] == MAX_flt)
				{
					FlowField[Surf] = FVector2D::ZeroVector; // absent surface — never sampled
					continue;
				}

				// Steepest descent for EVERY valid surface, including occupancy-blocked ones (DistField == MAX): an enemy
				// standing in a partially-obstructed surface still gets an escape direction toward the nearest reachable
				// open neighbour instead of zero flow (which would jam it against geometry). Codex.
				int32 BestDist = DistField[Surf];
				int32 BestNX = -1;
				int32 BestNY = -1;
				for (int32 N = 0; N < 8; ++N)
				{
					const int32 NX = CX + DX8[N];
					const int32 NY = CY + DY8[N];
					if (NX < 0 || NX >= GridDimX || NY < 0 || NY >= GridDimY)
					{
						continue;
					}
					const int32 NCell = NY * GridDimX + NX;
					if (N < 4)
					{
						// Orthogonal: consider each reachable neighbour rank. Don't point across a blocked edge (a thin
						// boundary wall the BFS routed around) unless THIS surface is itself blocked (keep escape).
						for (int32 RB = 0; RB < NumLayers; ++RB)
						{
							const int32 NSurf = SurfIndex(NCell, RB);
							if (CellFloorZ[NSurf] == MAX_flt)
							{
								continue;
							}
							if (!BlockedField[Surf] && !IsSurfaceEdgeTraversable(Cell, Rank, NCell, RB))
							{
								continue;
							}
							if (BlockedField[Surf] && FMath::Abs(CellFloorZ[NSurf] - CellFloorZ[Surf]) > RuntimeRampAllowance)
							{
								continue; // C5: too steep a rise/drop for a blocked surface's escape heading to use
							}
							if (DistField[NSurf] < BestDist)
							{
								BestDist = DistField[NSurf];
								BestNX = NX;
								BestNY = NY;
							}
						}
					}
					else if (Rank == 0)
					{
						// Diagonal corner-clearance — RANK 0 (ground plane) only; upper layers use 4-connected flow.
						const int32 NSurf = SurfIndex(NCell, 0);
						if (CellFloorZ[NSurf] == MAX_flt)
						{
							continue;
						}
						const int32 OrthoA = CY * GridDimX + NX; // (NX, CY)
						const int32 OrthoB = NY * GridDimX + CX; // (CX, NY)
						const int32 SA0 = SurfIndex(OrthoA, 0);
						const int32 SB0 = SurfIndex(OrthoB, 0);
						if (CellFloorZ[SA0] == MAX_flt || CellFloorZ[SB0] == MAX_flt || BlockedField[SA0] || BlockedField[SB0])
						{
							continue;
						}
						if (!BlockedField[Surf] &&
							(!IsSurfaceEdgeTraversable(Cell, 0, OrthoA, 0) || !IsSurfaceEdgeTraversable(Cell, 0, OrthoB, 0) ||
							 !IsSurfaceEdgeTraversable(OrthoA, 0, NCell, 0) || !IsSurfaceEdgeTraversable(OrthoB, 0, NCell, 0)))
						{
							continue;
						}
						if (BlockedField[Surf] && FMath::Abs(CellFloorZ[NSurf] - CellFloorZ[Surf]) > RuntimeRampAllowance)
						{
							continue; // C5: too steep a rise/drop for a blocked surface's escape heading to use
						}
						if (DistField[NSurf] < BestDist)
						{
							BestDist = DistField[NSurf];
							BestNX = NX;
							BestNY = NY;
						}
					}
				}

				// TOWER-PATH C4: also consider THIS surface's own active drop link(s) — a drop is not an EdgeMask
				// edge (IsSurfaceEdgeTraversable would reject it above), so without this the loops above would
				// never route flow across one even though RunBFS's own incoming-relax (above) already lets it
				// shorten the BFS distance. Skip a drop into a BLOCKED target — routing flow into occupied
				// geometry is the same mistake the orthogonal/diagonal loops already avoid.
				if (DropTarget.Num() == NumSurf * 4)
				{
					for (int32 N = 0; N < 4; ++N)
					{
						const int32 DropTgt = DropTarget[Surf * 4 + N];
						if (DropTgt == INDEX_NONE || BlockedField[DropTgt])
						{
							continue;
						}
						if (DistField[DropTgt] < BestDist)
						{
							BestDist = DistField[DropTgt];
							BestNX = CX + DX4[N];
							BestNY = CY + DY4[N];
						}
					}
				}

				if (BestNX >= 0)
				{
					const FVector2D Dir(static_cast<float>(BestNX - CX), static_cast<float>(BestNY - CY));
					FlowField[Surf] = Dir.GetSafeNormal();
				}
				else
				{
					FlowField[Surf] = FVector2D::ZeroVector; // at/near a source
				}
			}
		}
	}

	bFieldReady = true;
}
```
