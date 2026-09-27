# 코드 발췌 · 효과 계약과 적용 루프

[← 포트폴리오](../README.md) · [소스 출처](../SOURCE_MAP.md)

실제 커밋에서 가져온 읽기용 발췌입니다. include·선언·주변 초기화 등이 생략돼 독립 컴파일되지 않습니다. 테스트 발췌도 전체 fixture와 실행 결과를 포함하지 않습니다.

원본 파일의 고지: `// Copyright Epic Games, Inc. All Rights Reserved.`

## 서버 효과 문맥과 다형적 효과 계약

원본: `Source/FPSRoguelite/Public/Card/FPSRCardEffect.h` · L28–L102

```cpp
/** Server-side context for applying a card effect. Built on the server from the selecting player; never replicated
 *  (effects live as inline subobjects of an always-loaded card asset and never cross the wire). */
struct FFPSRCardEffectContext
{
	AController* Player = nullptr;
	AFPSRPlayerState* PS = nullptr;
	UFPSRAbilitySystemComponent* ASC = nullptr;
	UFPSRWeaponInventoryComponent* Inventory = nullptr;
	/** The weapon this card targets (weapon-group cards). null for character/all-weapons effects. */
	UFPSRWeaponDataAsset* TargetWeapon = nullptr;

	/** Index (into the target weapon's distinct-fragment list) of the fragment to DROP when granting a new behavior
	 *  fragment to a weapon already at its slot cap (U6 replacement flow). INDEX_NONE = no replacement (plain add /
	 *  under-cap). Server-validated against the resolved target weapon's list — a forged/out-of-range index is rejected. */
	int32 ReplaceFragmentIndex = INDEX_NONE;
};

/**
 * Polymorphic card effect (U18a, §2-3-1). A card owns an Instanced array of these; ApplyCard loops them
 * effect-type-agnostically (Apply / ResolveMagnitude). A NEW effect type = one subclass (~40 lines), zero central
 * edits (OCP / extensibility directive). Inline subobject of the card DataAsset — never replicated.
 */
UCLASS(Abstract, EditInlineNew, DefaultToInstanced, CollapseCategories)
class FPSROGUELITE_API UFPSRCardEffect : public UObject
{
	GENERATED_BODY()

public:
	/** Per-rarity magnitude for THIS effect. A card rolls one rarity (Card->OfferRarities); each effect reads its
	 *  own magnitude here — so two effects on one card can scale differently ("fire rate + / damage -"). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Card Effect")
	TArray<FFPSRCardRarityTier> RarityTiers;

	/** Magnitude for the given rolled rarity (0 if this effect declares no tier for it). The single source of an
	 *  effect's numeric value — Apply/GetDescription receive it pre-resolved so the central loop stays type-agnostic. */
	float ResolveMagnitude(ECardRarity Rarity) const;

	/** Server: apply this effect to the player. Magnitude is pre-resolved by the caller (ResolveMagnitude(Draw.Rarity)).
	 *  Must not fail once CanApply() returned true (the apply pass is transactional — see UFPSRCardSubsystem::ApplyCard). */
	virtual void Apply(const FFPSRCardEffectContext& Context, float Magnitude) const PURE_VIRTUAL(UFPSRCardEffect::Apply, );

	/** UI: a short auto-generated description line for this effect at the rolled rarity/magnitude (§2-3-8). */
	virtual FText GetDescription(ECardRarity Rarity, float Magnitude) const;

	/** Draw-time gate: does the player need to own a weapon for this effect to be meaningful? Mirrors v1's
	 *  "weapon-scope cards join the pool only once a weapon is owned" — effect-based so the routing is unchanged. */
	virtual bool RequiresWeapon() const { return false; }

	/** Apply-time gate: can this effect apply right now? Must be a COMPLETE precondition check (ASC/inventory/target
	 *  resolvable) so Apply() cannot fail afterwards — preserves the v1 reject-without-consume contract. */
	virtual bool CanApply(const FFPSRCardEffectContext& Context) const { return true; }

	/** Forward-compat elemental seam (§2-3-7): empty = Physical. U18a ships no elemental subclass. */
	virtual FGameplayTag GetDamageTypeTag() const { return FGameplayTag(); }

#if WITH_EDITOR
	/** Editor validation of this effect's OWN fields. Append errors/warnings to Context. */
	virtual void ValidateEffect(FDataValidationContext& Context) const {}

	/** Editor-tool grid label: a rarity-independent one-line identity of this effect for the Data Editor magnitude
	 *  grid's Summary column (e.g. "Character GE", "Weapon Stat: Damage (all weapons)"). Base = the effect's class
	 *  display name. Override per subclass. Editor-only; no runtime cost. */
	virtual FText GetEditorGridLabel() const;

	/** Editor-tool routing: which closed draw routes this effect PERMITS a card to be placed in. The Data Editor
	 *  intersects this across a card's effects for its wiring preflight (a card in an ineligible route is blocked).
	 *  Declared per subclass so a NEW effect type surfaces in the tool with zero central edits (OCP). Base = empty. */
	virtual TArray<EFPSRCardRoute> GetEditorEligibleRoutes() const;

	/** Editor-tool (P2): the unit this effect's RarityTiers magnitude is expressed in, for the Data Editor's bulk
	 *  arithmetic safety (additive bulk edits require a unit-homogeneous selection). Base = None (magnitude-agnostic
	 *  effect — grant/passive/behavior). Override per subclass that actually reads a numeric magnitude. */
	virtual EFPSREditorMagnitudeUnit GetEditorMagnitudeUnit() const;
#endif
};
```

## UFPSRCardSubsystem::ApplyCard

원본: `Source/FPSRoguelite/Private/Card/FPSRCardSubsystem.cpp` · L351–L431

```cpp
bool UFPSRCardSubsystem::ApplyCard(AController* ForPlayer, const FFPSRCardDraw& Draw, int32 ReplaceFragmentIndex)
{
	UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_Client)
	{
		return false;
	}

	UFPSRCardDataAsset* Card = Draw.Card;
	if (!Card || !ForPlayer)
	{
		return false;
	}

	AFPSRPlayerState* PS = ForPlayer->GetPlayerState<AFPSRPlayerState>();
	if (!PS)
	{
		return false;
	}

	UFPSRAbilitySystemComponent* ASC = PS->GetFPSRAbilitySystemComponent();
	if (!ASC)
	{
		return false;
	}

	// Build the server-side effect context (never replicated). The pawn's inventory + the draw's TargetWeapon let
	// weapon effects resolve their target; an unowned TargetWeapon resolves to null (anti-cheat: the offer was
	// server-built from owned weapons), so a forged target is rejected in pass 1 below.
	FFPSRCardEffectContext EffCtx;
	EffCtx.Player = ForPlayer;
	EffCtx.PS = PS;
	EffCtx.ASC = ASC;
	if (APawn* Pawn = ForPlayer->GetPawn())
	{
		EffCtx.Inventory = Pawn->FindComponentByClass<UFPSRWeaponInventoryComponent>();
	}
	EffCtx.TargetWeapon = Draw.TargetWeapon;
	EffCtx.ReplaceFragmentIndex = ReplaceFragmentIndex;

	if (Card->Effects.Num() == 0)
	{
		// Misconfigured card (IsDataValid guards authoring) — reject before applying any effects.
		return false;
	}

	// Pass 1: every effect must be applicable (CanApply = complete precondition: ASC / inventory / target instance
	// resolvable). If any can't, reject WITHOUT consuming — preserves the v1 "no weapon/instance -> offer stays up"
	// contract and makes the apply transactional (single-threaded server: no yield between passes, so no
	// partial-apply-then-fail).
	for (const TObjectPtr<UFPSRCardEffect>& Effect : Card->Effects)
	{
		if (Effect && !Effect->CanApply(EffCtx))
		{
			UE_LOG(LogFPSR, Verbose, TEXT("[Card] ApplyCard '%s' rejected: %s cannot apply (no effects applied)."),
				*Card->GetName(), *Effect->GetClass()->GetName());
			return false;
		}
	}

	// Pass 2: apply each effect with its OWN rolled-rarity magnitude (so multi-effect trade-offs scale independently).
	// No effect fails here — CanApply was the complete gate. Effect-type-agnostic: a new effect type needs no edit here.
	for (const TObjectPtr<UFPSRCardEffect>& Effect : Card->Effects)
	{
		if (!Effect)
		{
			continue;
		}
		const float Magnitude = Effect->ResolveMagnitude(Draw.Rarity);
		Effect->Apply(EffCtx, Magnitude);
		UE_LOG(LogFPSR, Log, TEXT("[Card] '%s': applied %s (mag %.2f)"),
			*Card->GetName(), *Effect->GetClass()->GetName(), Magnitude);
	}

	// CRIT2 §7 기록 시점 계약(익스플로잇 차단): 원장은 효과가 성공적으로 적용된 뒤에만 는다 — 효과 적용 뒤, return
	// true 앞. 제시만 받은 카드·거부된 픽·리롤로 버린 카드는 여기 도달하지 않으므로 기록되지 않는다. 이 서브시스템
	// 안이 유일 지점이다(디버그 FPSR.ApplyCard·교체 경로도 이 함수를 타므로 새어 나가지 않는다).
	PS->RecordAcquiredCard(Card, Draw.Rarity, Draw.TargetWeapon);

	return true;
}
```

## UFPSRCardSubsystem::ComputeSynergyMultiplier

원본: `Source/FPSRoguelite/Private/Card/FPSRCardSubsystem.cpp` · L52–L66

```cpp
float UFPSRCardSubsystem::ComputeSynergyMultiplier(const TArray<FName>& CardTags, const TMap<FName, int32>& TagCounts,
	float BonusPerCard, int32 MaxStacks)
{
	// 카드가 태그를 여러 개 달았으면 가장 많이 투자한 태그 하나만 본다(합산 아님, §6 헤더 주석) — 합산하면 저작이
	// "태그를 많이 달수록 유리"로 왜곡된다.
	int32 BestCount = 0;
	for (const FName& Tag : CardTags)
	{
		if (const int32* Count = TagCounts.Find(Tag))
		{
			BestCount = FMath::Max(BestCount, *Count);
		}
	}
	return 1.0f + BonusPerCard * static_cast<float>(FMath::Min(BestCount, MaxStacks));
}
```
