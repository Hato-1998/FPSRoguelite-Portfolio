# 코드 발췌 · 객체의 소유 관계와 일반 적의 기본 구성

[← 포트폴리오](../README.md) · [소스 출처](../SOURCE_MAP.md)

실제 커밋에서 가져온 읽기용 발췌입니다. include·선언·주변 초기화 등이 생략돼 독립 컴파일되지 않습니다. 테스트 발췌도 전체 fixture와 실행 결과를 포함하지 않습니다.

원본 파일의 고지: `// Copyright Epic Games, Inc. All Rights Reserved.`

## AFPSRPlayerState::AFPSRPlayerState

원본: `Source/FPSRoguelite/Private/Core/FPSRPlayerState.cpp` · L24–L36

```cpp
AFPSRPlayerState::AFPSRPlayerState()
{
	ShopComponent = CreateDefaultSubobject<UFPSRShopComponent>(TEXT("ShopComponent"));
	AbilitySystemComponent = CreateDefaultSubobject<UFPSRAbilitySystemComponent>(TEXT("AbilitySystemComponent"));
	AbilitySystemComponent->SetIsReplicated(true);
	AbilitySystemComponent->SetReplicationMode(EGameplayEffectReplicationMode::Mixed);

	HealthSet = CreateDefaultSubobject<UFPSRHealthSet>(TEXT("HealthSet"));
	CombatSet = CreateDefaultSubobject<UFPSRCombatSet>(TEXT("CombatSet"));

	// PlayerState updates frequently so GAS state stays responsive for clients.
	SetNetUpdateFrequency(100.0f);
}
```

## AFPSREnemyBase::AFPSREnemyBase

원본: `Source/FPSRoguelite/Private/Enemy/FPSREnemyBase.cpp` · L73–L131

```cpp
AFPSREnemyBase::AFPSREnemyBase()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;
	SetReplicateMovement(true);

	// DL-30 — 모든 플레이어는 같은 적 집합을 본다: 거리와 무관하게 모든 연결에 복제한다(보스와 같은 엔진 플래그).
	// 풀 적은 Deactivate 가 DORM_DormantAll 로 재워 복제 대상에서 빠진다(휴면은 relevancy 와 별개).
	// 공간 relevancy(RepGraph·경로 C)를 들이면 이 줄을 되돌린다 — 적 BP 는 엔진 "Always Relevant" 체크로 개별 해제 가능.
	bAlwaysRelevant = true;

	Capsule = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Capsule"));
	Capsule->InitCapsuleSize(40.0f, DefaultCapsuleHalfHeight);
	Capsule->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	Capsule->SetCollisionObjectType(ECC_Pawn);
	Capsule->SetCollisionResponseToAllChannels(ECR_Block);
	// Ignore OTHER enemies (also ECC_Pawn): the swarm overlaps and spreads via soft separation steering instead
	// of mutual physics blocking, which would gridlock a dense crowd and stack co-spawned enemies (Game.MD §1/§5).
	// Walls (WorldStatic), the rifle trace (Visibility) and the player (ECC_FPSRPlayerPawn) stay blocked.
	Capsule->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	SetRootComponent(Capsule);
	// Players must not stand on / step onto / use an enemy as a launch pad (9/23 playtest). AFPSREnemyBase is an
	// APawn, and engine APawn::CanBeBaseForCharacter (Engine/Private/Pawn.cpp) returns false when the ROOT
	// primitive's CanCharacterStepUpOn is ECB_No; UPrimitiveComponent::CanCharacterStepUp reads the same field, so
	// both CMC checks (CanStepUp, and ACharacter::BaseChange -> JumpOff) reject the enemy. A plain property read
	// only inside the PLAYER's movement code when it touches the enemy — no per-enemy tick cost (1000-enemy first
	// principle). Same pattern as ACharacter's own ctor (Engine/Private/Character.cpp) and AFPSRDefenseDome
	// (Private/Economy/FPSRDefenseDome.cpp).
	Capsule->CanCharacterStepUpOn = ECB_No;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Capsule);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetRelativeLocation(FVector(0.0f, 0.0f, -90.0f));
	Mesh->SetRelativeScale3D(FVector(0.8f, 0.8f, 1.8f));
	// Placeholder mesh is resolved in BeginPlay from config (Game.md §6-2: no hard-coded asset path in C++). Normal
	// enemy BPs assign their own (VAT) mesh, so the fallback only fires for the raw-C++ spawn (unconfigured roster).

	HealthComponent = CreateDefaultSubobject<UFPSREnemyHealthComponent>(TEXT("HealthComponent"));

	// HB1: native health-bar widget component — every AFPSREnemyBase-derived archetype gets one unconditionally
	// (net mode is unknown at ctor time; InitHealthBarWidget is what skips a dedicated server). Values below are
	// BP_EnemyMeleeBase's own MEASURED authoring (HB1 §6-1) copied verbatim, so this is a no-regression migration
	// for that archetype and a net-new (previously zero-cost, silently-missing) bar for the other two. The widget
	// CLASS itself is resolved later from config (InitHealthBarWidget), never here — no asset path in C++.
	HealthBarWidgetComponent = CreateDefaultSubobject<UWidgetComponent>(TEXT("HealthBarWidgetComponent"));
	HealthBarWidgetComponent->SetupAttachment(Capsule);
	HealthBarWidgetComponent->SetWidgetSpace(EWidgetSpace::Screen);
	HealthBarWidgetComponent->SetDrawSize(FVector2D(160.0f, 120.0f));
	HealthBarWidgetComponent->SetPivot(FVector2D(0.5f, 0.5f));
	HealthBarWidgetComponent->SetRelativeLocation(FVector(0.0f, 0.0f, 120.0f));
	HealthBarWidgetComponent->SetDrawAtDesiredSize(false);
	HealthBarWidgetComponent->SetTickWhenOffscreen(false);
	// Engine default TickMode is Enabled, which never self-gates on SetHiddenInGame — Automatic does
	// (WidgetComponent.cpp:1262's TickMode != Enabled guard), so a hidden-by-LOD bar's component tick actually
	// stops instead of ticking every frame regardless (HB1 §6-1/§10). Not dead code — see that section.
	HealthBarWidgetComponent->SetTickMode(ETickMode::Automatic);
	HealthBarWidgetComponent->SetHiddenInGame(false); // matches the 2-axis visibility contract's true/true initial state
}
```
