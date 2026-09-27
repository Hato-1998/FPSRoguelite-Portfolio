# 코드 발췌 · 구현 계약을 검사하는 회귀 테스트

[← 포트폴리오](../README.md) · [소스 출처](../SOURCE_MAP.md)

실제 커밋에서 가져온 읽기용 발췌입니다. include·선언·주변 초기화 등이 생략돼 독립 컴파일되지 않습니다. 테스트 발췌도 전체 fixture와 실행 결과를 포함하지 않습니다.

원본 파일의 고지: `// Copyright Epic Games, Inc. All Rights Reserved.`

## 정상 구매·재전송·효과 실패 환불

원본: `Source/FPSRoguelite/Private/Tests/FPSRShopTransactionsTest.cpp` · L103–L125

```cpp
	TestTrue(TEXT("server opens a registered in-range shop"), ShopState->OpenShop(Shop));
	TestEqual(TEXT("opening costs no coins"), PS->GetRunCoins(), InitialCoins);
	TestEqual(TEXT("initial normal offer has three cards"), ShopState->Snapshot.NormalOffers.Num(), 3);
	TestEqual(TEXT("owner snapshot matches wallet"), ShopState->Snapshot.Coins, InitialCoins);
	const int32 FirstRevision = ShopState->Snapshot.Revision;
	ShopState->ServerBuyCard(FirstRevision, 0, false);
	TestEqual(TEXT("normal card costs one coin"), PS->GetRunCoins(), InitialCoins - 1);
	TestEqual(TEXT("normal purchase applies a real weapon modifier"), PS->GetAllWeaponsMods().Mods.Num(), 1);
	TestEqual(TEXT("normal purchase records the acquired card"), PS->GetAcquiredCards().Num(), 1);
	TestEqual(TEXT("successful card purchase raises personal level"), PS->GetCardLevel(), 2);
	TestEqual(TEXT("normal purchase replaces all three slots"), ShopState->Snapshot.NormalOffers.Num(), 3);
	TestEqual(TEXT("purchase keeps free rerolls"), PS->GetRunRerollCharges(), 3);
	ShopState->ServerBuyCard(FirstRevision, 0, false);
	TestEqual(TEXT("replayed revision cannot buy again"), PS->GetRunCoins(), InitialCoins - 1);
	ShopState->ServerBuyCard(ShopState->Snapshot.Revision, 99, false);
	TestEqual(TEXT("forged index cannot spend"), PS->GetRunCoins(), InitialCoins - 1);

	// A real ApplyCard rejection must restore the debit and preserve its offer.
	UFPSRCardDataAsset* InvalidCard = NewObject<UFPSRCardDataAsset>(World);
	ShopState->Snapshot.NormalOffers[0].Card = InvalidCard;
	ShopState->ServerBuyCard(ShopState->Snapshot.Revision, 0, false);
	TestEqual(TEXT("failed effect application refunds the reservation"), PS->GetRunCoins(), InitialCoins - 1);
	TestTrue(TEXT("failed effect application keeps its offer"), ShopState->Snapshot.NormalOffers[0].Card == InvalidCard);
```

## 상속 관계여도 정확한 클래스만 반환

원본: `Source/FPSRoguelite/Private/Tests/FPSREnemyDormantPoolTest.cpp` · L98–L116

```cpp
	// --- (5) THE core property this test exists for: an elite request must not pick up a normal enemy, even
	//         though AFPSREnemyEliteBase IS a child of AFPSREnemyBase (an IsChildOf-based implementation would
	//         satisfy this substitutability and pass a normal instance off as the elite that was asked for — or,
	//         the other direction, hand an elite instance to a plain request). Isolated single-class pools make
	//         either direction of that bug unmissable: the ONLY entry present is the wrong class, so any non-null
	//         return is necessarily the bug. -----------------------------------------------------------------
	{
		FFPSREnemyDormantPool NormalOnlyPool;
		NormalOnlyPool.Add(NormalCdo);
		TestNull(TEXT("(5) elite request against a NORMAL-only pool must be null — must NOT return the normal CDO"),
			NormalOnlyPool.AcquireOfClass(EliteClass));
		TestEqual(TEXT("(5) the rejected elite request must not have consumed the normal entry"), NormalOnlyPool.Num(), 1);

		FFPSREnemyDormantPool EliteOnlyPool;
		EliteOnlyPool.Add(EliteCdo);
		TestNull(TEXT("(5) normal request against an ELITE-only pool must be null — must NOT return the elite CDO"),
			EliteOnlyPool.AcquireOfClass(NormalClass));
		TestEqual(TEXT("(5) the rejected normal request must not have consumed the elite entry"), EliteOnlyPool.Num(), 1);
	}
```

## 발 높이에 맞는 데크 표면 선택

원본: `Source/FPSRoguelite/Private/Tests/FPSRFlowFieldTowerPathTest.cpp` · L61–L79

```cpp
	// ---- (1) C1: ResolveSourceSurface anchors the ring search on the pawn's FOOT Z (not the cell's own rank0)
	//     when the pawn's own cell has no surface within pick range — a raised deck over a ground-only cell. ----
	{
		// 2x1: Cell0 = ground-only (no deck). Cell1 = ground (rank0=0) + deck (rank1=1000).
		FFPSRFlowFieldSurfaceData D = MakeEmptyGridTP(2, 1, Cell, FVector::ZeroVector);
		D.CellFloorZ[SurfTP(0, 0)] = 0.0f;
		D.CellFloorZ[SurfTP(1, 0)] = 0.0f;
		D.CellFloorZ[SurfTP(1, 1)] = 1000.0f;

		TStrongObjectPtr<UFPSRFlowFieldComputer> C(NewObject<UFPSRFlowFieldComputer>());
		C->BuildFromSurfaceData(D);

		// Pawn stands over Cell0 (ground-only) but at deck height (foot Z 1000) — e.g. leaning out over a deck
		// edge above a lower floor. World == nullptr: the worldless test seam (LOS always passes).
		const int32 Resolved = C->ResolveSourceSurface(nullptr, FVector(50.0f, 50.0f, 1000.0f), 0.0f);
		TestTrue(TEXT("C1: a surface was resolved"), Resolved != INDEX_NONE);
		TestEqual(TEXT("C1: resolves to the DECK surface (Z 1000), not the ground below it"),
			C->GetCellFloorZ(Resolved), 1000.0f);
	}
```
