# 코드 발췌 · 서버 상점의 검증·구매·복제

[← 포트폴리오](../README.md) · [소스 출처](../SOURCE_MAP.md)

실제 커밋에서 가져온 읽기용 발췌입니다. include·선언·주변 초기화 등이 생략돼 독립 컴파일되지 않습니다. 테스트 발췌도 전체 fixture와 실행 결과를 포함하지 않습니다.

원본 파일의 고지: `// Copyright Epic Games, Inc. All Rights Reserved.`

## UFPSRShopComponent::GetLifetimeReplicatedProps

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L25–L32

```cpp
void UFPSRShopComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	FDoRepLifetimeParams Params;
	Params.bIsPushBased = true;
	Params.Condition = COND_OwnerOnly;
	DOREPLIFETIME_WITH_PARAMS_FAST(UFPSRShopComponent, Snapshot, Params);
}
```

## UFPSRShopComponent::GetShopController

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L39–L44

```cpp
APlayerController* UFPSRShopComponent::GetShopController() const
{
	const AFPSRPlayerState* PS = GetShopPlayerState();
	APlayerController* PC = PS ? Cast<APlayerController>(PS->GetOwner()) : nullptr;
	return PC && PC->GetPlayerState<AFPSRPlayerState>() == PS ? PC : nullptr;
}
```

## UFPSRShopComponent::IsSessionValid

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L72–L84

```cpp
bool UFPSRShopComponent::IsSessionValid() const
{
	const AFPSRPlayerState* PS = GetShopPlayerState();
	APlayerController* PC = GetShopController();
	APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	if (!PS || !PS->HasAuthority() || PS->IsOnlyASpectator() || PS->IsInactive()
		|| !IsValid(Pawn) || Pawn != SessionPawn.Get() || Pawn->GetPlayerState() != PS || !IsValid(Snapshot.Shop))
	{
		return false;
	}
	const UFPSRInteractionComponent* Interaction = Pawn->FindComponentByClass<UFPSRInteractionComponent>();
	return Interaction && Interaction->CanOwnerInteractWith(Snapshot.Shop);
}
```

## UFPSRShopComponent::GetPrice

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L86–L94

```cpp
int32 UFPSRShopComponent::GetPrice(EFPSRShopItem Item) const
{
	const UFPSRShopCatalogDataAsset* Catalog = IsValid(Snapshot.Shop) ? Snapshot.Shop->GetCatalog() : nullptr;
	const FFPSRShopEntry* Entry = Catalog ? Catalog->FindEntry(Item) : nullptr;
	if (!Entry || Entry->PriceCoins < 0) return -1;
	if (Item == EFPSRShopItem::Weapon) return Catalog->GetUnlockPrice(Snapshot.UnlockDrawsPurchased);
	if (Item == EFPSRShopItem::DefenseDome && !Catalog->DomeClass) return -1;
	return Entry->PriceCoins;
}
```

## UFPSRShopComponent::Publish

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L96–L116

```cpp
void UFPSRShopComponent::Publish()
{
	AFPSRPlayerState* PS = GetShopPlayerState();
	if (!PS || !PS->HasAuthority()) return;
	// Never wrap a signed integer. Exhaustion closes the session and permanently refuses requests for this PS.
	if (Snapshot.Revision < MAX_int32) ++Snapshot.Revision;
	else
	{
		Snapshot.Shop = nullptr;
		SessionPawn.Reset();
		GetWorld()->GetTimerManager().ClearTimer(SessionTimer);
	}
	Snapshot.Coins = PS->GetRunCoins();
	Snapshot.RerollCharges = PS->GetRunRerollCharges();
	Snapshot.CardPrice = GetPrice(EFPSRShopItem::CardDraw);
	Snapshot.UnlockPrice = GetPrice(EFPSRShopItem::Weapon);
	Snapshot.DomePrice = GetPrice(EFPSRShopItem::DefenseDome);
	Snapshot.RevivePrice = GetPrice(EFPSRShopItem::RemoteRevive);
	MARK_PROPERTY_DIRTY_FROM_NAME(UFPSRShopComponent, Snapshot, this);
	OnShopChanged.Broadcast();
}
```

## UFPSRShopComponent::CanRequest

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L181–L190

```cpp
bool UFPSRShopComponent::CanRequest(int32 Revision)
{
	if (bTransactionInProgress || Revision == MAX_int32 || Revision != Snapshot.Revision) return false;
	if (!IsSessionValid())
	{
		if (Snapshot.Shop) CloseShop();
		return false;
	}
	return true;
}
```

## UFPSRShopComponent::Debit

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L192–L195

```cpp
bool UFPSRShopComponent::Debit(int32 Price)
{
	return Price >= 0 && (Price == 0 || GetShopPlayerState()->TrySpendRunCoins(Price));
}
```

## UFPSRShopComponent::Refund

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L197–L200

```cpp
void UFPSRShopComponent::Refund(int32 Price)
{
	if (Price > 0) GetShopPlayerState()->RefundShopCoins(Price);
}
```

## UFPSRShopComponent::ServerBuyCard_Implementation

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L202–L230

```cpp
void UFPSRShopComponent::ServerBuyCard_Implementation(int32 Revision, int32 Index, bool bUnlock, int32 ReplaceFragmentIndex)
{
	if (!CanRequest(Revision)) return;
	const TArray<FFPSRCardDraw>& Offers = bUnlock ? Snapshot.UnlockOffers : Snapshot.NormalOffers;
	const int32 Price = GetPrice(bUnlock ? EFPSRShopItem::Weapon : EFPSRShopItem::CardDraw);
	UFPSRCardSubsystem* Cards = GetWorld()->GetSubsystem<UFPSRCardSubsystem>();
	if (!Offers.IsValidIndex(Index) || Price < 0 || !Cards
		|| (bUnlock && Snapshot.UnlockDrawsPurchased == MAX_int32)) return;
	const FFPSRCardDraw Draw = Offers[Index]; // callbacks can replace/reset the UPROPERTY array
	TGuardValue<bool> Lock(bTransactionInProgress, true);
	const uint32 Generation = RunGeneration;
	if (!Debit(Price)) return;
	const bool bApplied = IsSessionValid() && Generation == RunGeneration
		&& Cards->ApplyCard(GetShopController(), Draw, ReplaceFragmentIndex);
	if (!bApplied)
	{
		Refund(Price);
	}
	else if (Generation == RunGeneration)
	{
		if (bUnlock)
		{
			++Snapshot.UnlockDrawsPurchased;
			Snapshot.UnlockOffers = Cards->DrawWeaponUnlockOffer(GetShopController(), 3);
		}
		else Snapshot.NormalOffers = Cards->DrawCards(GetShopController(), 3);
	}
	Publish();
}
```

## UFPSRShopComponent::ResetForRun

원본: `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` · L156–L164

```cpp
void UFPSRShopComponent::ResetForRun()
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) return;
	++RunGeneration;
	Snapshot.NormalOffers.Reset();
	Snapshot.UnlockOffers.Reset();
	Snapshot.UnlockDrawsPurchased = 0;
	CloseShop();
}
```

## 소유자에게 복제하는 Snapshot

원본: `Source/FPSRoguelite/Public/Economy/FPSRShopComponent.h` · L14–L32

```cpp
USTRUCT(BlueprintType)
struct FFPSRShopSnapshot
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) TObjectPtr<AFPSRShopActor> Shop;
	UPROPERTY(BlueprintReadOnly) int32 Revision = 0;
	UPROPERTY(BlueprintReadOnly) TArray<FFPSRCardDraw> NormalOffers;
	UPROPERTY(BlueprintReadOnly) TArray<FFPSRCardDraw> UnlockOffers;
	/** Successful unlock card purchases. Kept under its serialized name for existing assets. */
	UPROPERTY(BlueprintReadOnly) int32 UnlockDrawsPurchased = 0;
	UPROPERTY(BlueprintReadOnly) int32 Coins = 0;
	UPROPERTY(BlueprintReadOnly) int32 RerollCharges = 0;
	UPROPERTY(BlueprintReadOnly) int32 CardPrice = -1;
	UPROPERTY(BlueprintReadOnly) int32 UnlockPrice = -1;
	UPROPERTY(BlueprintReadOnly) int32 DomePrice = -1;
	UPROPERTY(BlueprintReadOnly) int32 RevivePrice = -1;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FFPSROnShopChanged);
```
