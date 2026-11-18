# ProjectEGO · Gameplay Programming Portfolio

**Unreal Engine 5.8 · C++ · GAS · 2026.05 ~ 진행 중 · 리포 이름 FPSRoguelite**

ProjectEGO는 개인 프로젝트입니다. 이 저장소는 소스 코드를 공개하지 않고, 프로그래밍 구조와 설계 판단을 문서와 다이어그램으로만 설명합니다. 기준일은 **2026-11-18**입니다.

## 프로젝트 소개

**현재 단계 (2026.11 ~)**

- 1~4인이 하나의 신체를 공유하는 협동 FPS
- 손에 든 무기의 탄창이 비면 다른 플레이어에게 무작위로 조종이 넘어감
- 기다리는 플레이어는 머리 위 고리에 떠 있는 자기 무기로 계속 사격
- 현재 2인 최소 통합 단계

**이전 단계 (2026.05 ~ 11)**

- 협동 스타일 랭크 FPS로 프로토타입을 진행
- 핵심 재미를 먼저 검증하지 않고 시스템을 넓혀 프로토타입에 머묾
- 2026.11에 범위를 하나의 기믹으로 좁혀 재정의. 이동·사격 감각과 엔진 기반 코드는 이어받음

**규모와 역할**

- 커밋 3,323개(2026-11-18), 자동화 시험 944/944 통과(2026-11-14)
- 방향·설계 판단과 검증을 맡고, 구현은 AI 에이전트에 위임합니다([07](docs/07-ai-assisted-workflow.md))

## 이전 단계와 현재 단계의 관계

현재 단계는 이전 단계를 버리고 새로 시작한 것이 아니라, 이전 단계에서 검증한 부분을 이어받은 것입니다. 이동 상태의 단일 소유(01), 판정과 연출의 분리(02), 방 세이브 보호(05), 디버깅·측정 규율(06)은 이전 단계에서 만들어 현재 단계에서도 쓰는 설계입니다. 데이터 주도 파츠 빌드(03)는 이전 단계의 시스템이며 현재 단계에서는 꺼 둡니다. 공유 신체의 소유권(04)은 현재 단계에서 새로 설계하고 있는 부분입니다.

## 문서 목록

| 문서 | 문제 | 선택 | 단계 |
|---|---|---|---|
| [01 이동 상태의 단일 소유](docs/01-movement-state-ownership.md) | 새 이동 상태가 생길 때마다 사격·애님·HUD 코드가 함께 바뀜 | 무브먼트 컴포넌트 하나가 상태를 결정하고 다른 시스템은 질의 함수로만 읽음 | 이전, 현재로 이어짐 |
| [02 판정과 연출의 책임 분리](docs/02-fire-authority-presentation.md) | 서버가 판정을 확정하되 쏘는 사람은 즉시 반응해야 함 | 사수의 발사 연출은 예측으로 즉시, 팀원은 서버 확정으로. 명중은 예측하지 않음 | 이전, 현재로 이어짐 |
| [03 데이터 주도 파츠 빌드](docs/03-data-driven-parts.md) | 총 1정의 성장을 파츠로 표현하고 수치를 반복 조정 | 정의는 후보 축·효과만 갖고 (정의, 등급, 씨앗)에서 결정적으로 풀어 모든 기기가 같은 값 | 이전(현재 쓰지 않음) |
| [04 공유 신체의 소유권](docs/04-shared-body-ownership.md) | 여러 참가자가 하나의 몸을 번갈아 조종하되 각자의 시선·무기·HUD는 유지 | 참가자는 자기 Pawn을 계속 소유하고 서버는 신체의 운전자만 교체. 측정으로 진행 여부 판정 | 현재(진행 중) |
| [05 방 세이브 보호](docs/05-room-save-protection.md) | 저장 실패 뒤의 리셋이 방 상태를 버리는 결함 | 읽지 못한 슬롯에는 쓰지 않고 원본을 검증된 격리 사본으로 보존. 보존 실패 시 쓰기 차단 | 이전, 현재로 이어짐 |
| [06 디버깅과 성능 측정](docs/06-debugging-and-measurement.md) | 패키지에서만 나는 GC 크래시, 절벽 진입 시 슬라이딩 종료, 렌더 비용, 스웜 규모 | 재현 조건을 고정하고 측정으로 판단. 폐기한 구조는 단독 컴파일 등으로 안전하게 삭제 | 이전, 현재로 이어짐 |
| [07 AI 협업 개발 체계](docs/07-ai-assisted-workflow.md) | 구현을 AI에 위임하면서 결과를 믿을 수 있어야 함 | 감독·주 작업자·하위 작업자의 3층, 고위험 변경은 별도 인스턴스의 독립 검토를 거쳐야 병합 | 이전부터 현재까지 |

각 문서는 "문제 → 제약 → 선택한 구조 → 검토한 대안과 기각 이유 → 검증 → 한계와 남은 일" 순서로 씁니다. 설계 승인, 구현, 실행 검증, 미검증은 구분해 적었습니다. 04는 현재 진행 중인 설계라 "현재 상태와 미검증 항목"을 따로 두었습니다.

`C++` · `Gameplay Ability System` · `Server Authority` · `Client Prediction` · `Data Assets` · `Deterministic Roll` · `Automation Framework` · `Unreal Insights` · `AI-assisted Development`

**기준일: 2026-11-18.** [공개 범위와 권리 고지](NOTICE.md)

**English overview:** A documentation-only programming portfolio for *ProjectEGO* (repository name FPSRoguelite), an Unreal Engine 5.8 co-op FPS. The current stage is a shared-body co-op FPS in which one to four players take turns driving a single body; the previous stage was a co-op style-rank FPS prototype whose movement, fire and engine-foundation code carried over. The seven documents cover single-owner movement state, separation of server-authoritative hit decisions from owner-predicted presentation, a data-driven parts build with deterministic rolls, ownership of the shared body (in progress, with open measurements), room-save protection, debugging and measurement cases, and the AI-assisted workflow. No source code or assets are distributed, and no demo has been released.
