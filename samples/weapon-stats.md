# 코드 발췌 · 복제 입력과 지연 계산 캐시

[← 포트폴리오](../README.md) · [소스 출처](../SOURCE_MAP.md)

실제 커밋에서 가져온 읽기용 발췌입니다. include·선언·주변 초기화 등이 생략돼 독립 컴파일되지 않습니다. 테스트 발췌도 전체 fixture와 실행 결과를 포함하지 않습니다.

원본 파일의 고지: `// Copyright Epic Games, Inc. All Rights Reserved.`

## UFPSRWeaponInstance::OnRep_Source

원본: `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` · L274–L277

```cpp
void UFPSRWeaponInstance::OnRep_Source()
{
	MarkResolvedDirty();
}
```

## UFPSRWeaponInstance::OnRep_Modifiers

원본: `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` · L279–L283

```cpp
void UFPSRWeaponInstance::OnRep_Modifiers()
{
	MarkResolvedDirty();
	NotifyOwnerModifiersChanged();
}
```

## UFPSRWeaponInstance::OnRep_ActiveFragments

원본: `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` · L285–L289

```cpp
void UFPSRWeaponInstance::OnRep_ActiveFragments()
{
	MarkResolvedDirty();
	NotifyOwnerModifiersChanged();
}
```

## UFPSRWeaponInstance::GetResolvedStats

원본: `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` · L304–L312

```cpp
const FFPSRWeaponStatBlock& UFPSRWeaponInstance::GetResolvedStats()
{
	if (bResolvedDirty)
	{
		RecomputeResolved();
		bResolvedDirty = false;
	}
	return CachedResolved;
}
```

## UFPSRWeaponInstance::RecomputeResolved

원본: `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` · L330–L420

```cpp
void UFPSRWeaponInstance::RecomputeResolved()
{
	if (!Source)
	{
		CachedResolved = FFPSRWeaponStatBlock();
		return;
	}

	CachedResolved = Source->BaseStats;

	// Accumulate additive and percent contributions per axis from ThisWeapon (this instance) and AllWeapons
	// (owning PlayerState) modifier stacks.
	struct FAxisAccum { float Add = 0.0f; float Pct = 0.0f; };
	// Keyed by the enum's integer value to avoid relying on enum-class TMap hashing.
	TMap<int32, FAxisAccum> Accum;

	// Exclusions (optional) drop mods on listed axes — used ONLY for the AllWeapons stack, so a broad "all weapons"
	// card can't touch an axis the weapon opted out of (e.g. ChargeLaser recoil). ThisWeapon mods always apply.
	auto GatherStack = [&Accum](const FFPSRWeaponModContainer& Container, const TArray<EFPSRWeaponStat>* Exclusions)
	{
		for (const FFPSRWeaponStatMod& Mod : Container.Mods)
		{
			if (Exclusions && Exclusions->Contains(Mod.Stat))
			{
				continue; // this weapon opts out of AllWeapons mods on this axis
			}
			FAxisAccum& A = Accum.FindOrAdd(static_cast<int32>(Mod.Stat));
			if (Mod.Op == EFPSRWeaponModOp::Additive)
			{
				A.Add += Mod.Value;
			}
			else
			{
				A.Pct += Mod.Value;
			}
		}
	};

	GatherStack(Modifiers, nullptr); // ThisWeapon: never filtered (deliberately targeted at this weapon)
	if (const AFPSRPlayerState* PS = ResolveOwningPlayerState())
	{
		GatherStack(PS->GetAllWeaponsMods(), &Source->AllWeaponsStatExclusions);
	}

	for (const TPair<int32, FAxisAccum>& Pair : Accum)
	{
		const float Add = Pair.Value.Add;
		const float Mult = 1.0f + Pair.Value.Pct;
		switch (static_cast<EFPSRWeaponStat>(Pair.Key))
		{
		case EFPSRWeaponStat::MagSize:
			CachedResolved.MagSize = FMath::Max(1, FMath::RoundToInt((CachedResolved.MagSize + Add) * Mult));
			break;
		case EFPSRWeaponStat::FireRate:
			CachedResolved.FireRate = FMath::Max(0.01f, (CachedResolved.FireRate + Add) * Mult);
			break;
		case EFPSRWeaponStat::RecoilVertical:
			CachedResolved.RecoilVertical = FMath::Max(0.0f, (CachedResolved.RecoilVertical + Add) * Mult);
			break;
		case EFPSRWeaponStat::Damage:
			CachedResolved.Damage = FMath::Max(0.0f, (CachedResolved.Damage + Add) * Mult);
			break;
		case EFPSRWeaponStat::SpreadDegrees:
			CachedResolved.SpreadDegrees = FMath::Max(0.0f, (CachedResolved.SpreadDegrees + Add) * Mult);
			break;
		case EFPSRWeaponStat::ReloadTime:
			CachedResolved.ReloadTime = FMath::Max(0.0f, (CachedResolved.ReloadTime + Add) * Mult);
			break;
		case EFPSRWeaponStat::ShieldDamageMultiplier:
			CachedResolved.ShieldDamageMultiplier = FMath::Max(0.0f, (CachedResolved.ShieldDamageMultiplier + Add) * Mult);
			break;
		case EFPSRWeaponStat::ADSFieldOfView:
			// Clamp is mandatory (P-C): FOV stacking to 0/negative would break the camera. Lower bound 5 degrees is
			// roughly a 20x zoom — far past any authored scope tier, so it only ever fires on a pathological stack.
			CachedResolved.ADSFieldOfView = FMath::Clamp((CachedResolved.ADSFieldOfView + Add) * Mult, 5.0f, 170.0f);
			break;
		default:
			break;
		}
	}

	// Behavior fragments may override the resolved fire mode (e.g. a Burst fragment flips FullAuto -> Burst). Applied
	// after numeric stats so the fire component — which reads CachedResolved.FireMode/BurstCount — needs no extra wiring.
	for (const TObjectPtr<UFPSRWeaponFragment>& Frag : ActiveFragments)
	{
		if (Frag)
		{
			Frag->ModifyFireMode(CachedResolved.FireMode, CachedResolved.BurstCount);
		}
	}
}
```
