# 소스 출처와 발췌 기준

[← 포트폴리오](README.md)

기준 날짜: **2026-09-27**. 기준 원본 커밋: `a6f03809b0fc3a0afdde3495e0e54f42742d4982`. 원본 저장소는 비공개이므로 접근할 수 없는 GitHub 링크 대신 프로젝트 상대 경로·줄 범위와 공개된 발췌를 제공합니다. 미커밋 작업은 포함하지 않았습니다.

줄 범위는 위 커밋의 원본 기준입니다. 개행만 LF로 정규화했으며 코드와 주석을 바꾸지 않았습니다. 코드 블록별 SHA-256은 [manifest](source-manifest.json)에 있습니다. 각 발췌는 부분 코드로서 완전한 클래스나 빌드 단위가 아닐 수 있습니다.

| 공개 발췌 | 원본 경로 | 원본 줄 |
|---|---|---|
| [enemy-pool · FFPSREnemyDormantPool::Add](samples/enemy-pool.md) | `Source/FPSRoguelite/Private/Enemy/FPSREnemyDormantPool.cpp` | 6–17 |
| [enemy-pool · FFPSREnemyDormantPool::AcquireOfClass](samples/enemy-pool.md) | `Source/FPSRoguelite/Private/Enemy/FPSREnemyDormantPool.cpp` | 19–49 |
| [enemy-pool · FFPSREnemyDormantPool::EvictOneFromLargestOtherBucket](samples/enemy-pool.md) | `Source/FPSRoguelite/Private/Enemy/FPSREnemyDormantPool.cpp` | 51–93 |
| [enemy-pool · FFPSREnemyDormantPool::Num](samples/enemy-pool.md) | `Source/FPSRoguelite/Private/Enemy/FPSREnemyDormantPool.cpp` | 95–103 |
| [flow-field · UFPSRFlowFieldComputer::RebuildDropLinks](samples/flow-field.md) | `Source/FPSRoguelite/Private/Enemy/FPSRFlowFieldComputer.cpp` | 215–303 |
| [flow-field · UFPSRFlowFieldComputer::RunBFS](samples/flow-field.md) | `Source/FPSRoguelite/Private/Enemy/FPSRFlowFieldComputer.cpp` | 464–701 |
| [shop-transactions · UFPSRShopComponent::GetLifetimeReplicatedProps](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 25–32 |
| [shop-transactions · UFPSRShopComponent::GetShopController](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 39–44 |
| [shop-transactions · UFPSRShopComponent::IsSessionValid](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 72–84 |
| [shop-transactions · UFPSRShopComponent::GetPrice](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 86–94 |
| [shop-transactions · UFPSRShopComponent::Publish](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 96–116 |
| [shop-transactions · UFPSRShopComponent::CanRequest](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 181–190 |
| [shop-transactions · UFPSRShopComponent::Debit](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 192–195 |
| [shop-transactions · UFPSRShopComponent::Refund](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 197–200 |
| [shop-transactions · UFPSRShopComponent::ServerBuyCard_Implementation](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 202–230 |
| [shop-transactions · UFPSRShopComponent::ResetForRun](samples/shop-transactions.md) | `Source/FPSRoguelite/Private/Economy/FPSRShopComponent.cpp` | 156–164 |
| [shop-transactions · 소유자에게 복제하는 Snapshot](samples/shop-transactions.md) | `Source/FPSRoguelite/Public/Economy/FPSRShopComponent.h` | 14–32 |
| [card-effects · 서버 효과 문맥과 다형적 효과 계약](samples/card-effects.md) | `Source/FPSRoguelite/Public/Card/FPSRCardEffect.h` | 28–102 |
| [card-effects · UFPSRCardSubsystem::ApplyCard](samples/card-effects.md) | `Source/FPSRoguelite/Private/Card/FPSRCardSubsystem.cpp` | 351–431 |
| [card-effects · UFPSRCardSubsystem::ComputeSynergyMultiplier](samples/card-effects.md) | `Source/FPSRoguelite/Private/Card/FPSRCardSubsystem.cpp` | 52–66 |
| [weapon-stats · UFPSRWeaponInstance::OnRep_Source](samples/weapon-stats.md) | `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` | 274–277 |
| [weapon-stats · UFPSRWeaponInstance::OnRep_Modifiers](samples/weapon-stats.md) | `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` | 279–283 |
| [weapon-stats · UFPSRWeaponInstance::OnRep_ActiveFragments](samples/weapon-stats.md) | `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` | 285–289 |
| [weapon-stats · UFPSRWeaponInstance::GetResolvedStats](samples/weapon-stats.md) | `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` | 304–312 |
| [weapon-stats · UFPSRWeaponInstance::RecomputeResolved](samples/weapon-stats.md) | `Source/FPSRoguelite/Private/Weapon/FPSRWeaponInstance.cpp` | 330–420 |
| [ownership · AFPSRPlayerState::AFPSRPlayerState](samples/ownership.md) | `Source/FPSRoguelite/Private/Core/FPSRPlayerState.cpp` | 24–36 |
| [ownership · AFPSREnemyBase::AFPSREnemyBase](samples/ownership.md) | `Source/FPSRoguelite/Private/Enemy/FPSREnemyBase.cpp` | 73–131 |
| [regression-tests · 정상 구매·재전송·효과 실패 환불](samples/regression-tests.md) | `Source/FPSRoguelite/Private/Tests/FPSRShopTransactionsTest.cpp` | 103–125 |
| [regression-tests · 상속 관계여도 정확한 클래스만 반환](samples/regression-tests.md) | `Source/FPSRoguelite/Private/Tests/FPSREnemyDormantPoolTest.cpp` | 98–116 |
| [regression-tests · 발 높이에 맞는 데크 표면 선택](samples/regression-tests.md) | `Source/FPSRoguelite/Private/Tests/FPSRFlowFieldTowerPathTest.cpp` | 61–79 |

구조 설명에는 동일 커밋의 모듈 정의, 클래스 선언, 호출부도 참조했습니다. 공개본은 전체 소스 미러가 아니므로 발췌 밖 클래스와 함수는 설명에서만 등장할 수 있습니다. 문서는 새로 작성했으며 비공개 설계 문서를 통째로 복제하지 않았습니다.
