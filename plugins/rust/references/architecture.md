# Architecture 판단 기준

목표는 폴더 수가 아니라 **책임의 응집도, 호출자에게 주는 이점, 변경의 국소성**이다. 이 문서는 overview다.
구체적인 프로젝트 결정은 ADR (look up `docs/adr/README.md` in the consuming repository; its current project guidance remains authoritative), 유지할 행동 계약은 specs (look up `docs/specs/README.md` in the consuming repository; its current project guidance remains authoritative), 실제 package와
명령은 프로젝트 README (look up `README.md` in the consuming repository; its current project guidance remains authoritative)에 둔다. 공통 review 기준은 설치된 common plugin의 resource를
plugin routing (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative)으로 찾아 확인한다. 예시는 해당 기능이 구현되었다는 뜻이 아니다.

## Repository groups and native package

Standalone은 root `src/`를 product source의 출발점으로 삼고, monorepo는 `apps/`와 `packages/` 아래에서
application과 재사용 package 책임을 구분한다. 이 바깥 분류가 언어의 native layout을 없애지는 않는다.

| 선택한 package | Native 경계의 예 |
| --- | --- |
| Python | standalone `src/package_name/`; mono package 안의 `src/package_name/`, manifest와 tests |
| TypeScript/React | package `src/`와 `package.json`; 실제 선택한 Node/browser/bundler의 resolution |
| Rust | 기본 package의 `src/lib.rs` + `src/main.rs`, `Cargo.toml`, features/targets와 tests |
| Firmware, 해당할 때 | 선택한 tool의 native source/config, board/environment와 calibration·safe-state 계약 |

예를 들어 `apps/api/`는 저장소의 실행 단위이고 `apps/api/src/api_service/`는 Python import source다.
별도의 바깥 `src/` wrapper는 필요하지 않다. 폴더만으로 package, workspace, FFI 또는 deployment가 만들어지지 않는다. Root `scripts/`와 `bin/`은
maintenance/명령 진입점이며 product logic의 우회 배치가 아니다. 선택하지 않은 package나 빈 domain layer는 만들지 않는다.

## 기본값: 작은 package와 명확한 책임

작은 library는 이해하기 쉬운 public API와 내부 module이면 충분하다. 작은 API/service는 boundary 변환,
이름 있는 operation과 구체적인 I/O collaborator로 시작한다. 다음 관계는 책임의 예시이지 각 항목을 파일이나
interface로 만드는 명령이 아니다.

```text
entrypoint/composition -> boundary -> operation/policy -> concrete I/O collaborator
```

정책이 독립적으로 바뀌거나 여러 I/O 구현, 복잡한 state invariant, 좁은 테스트가 과도한 setup을 요구할 때
필요한 경계를 추출한다. 추출 전후의 errors, validation, ordering과 lifecycle은 보존한다. ABC, trait,
generic repository 또는 DI framework는 경계를 이해시키는 실제 이점이 있을 때만 쓴다.

## 복잡한 backend는 선택적으로 domain 중심

- **Boundary**는 HTTP/CLI/message 입력, admission과 외부 error/response 변환을 소유한다.
- **Use case/service**는 사용자 작업과 orchestration을 소유하고 외부 framework 객체를 정책으로 흘리지 않는다.
- **Domain/policy**는 용어·불변조건·결정을 소유한다. 외부 I/O와 framework 의존을 안쪽에 넣지 않는다.
- **Repository/adapter**는 저장·외부 I/O 계약을 소유하며 두 번째 business authority를 만들지 않는다.
- **Composition**은 구체적인 collaborator와 자원 수명을 연결한다.

이 구분은 기본 skeleton에 미리 `domain/` 등을 만들 이유가 아니다. 현재 선택한 DTO/model을 순수성 명목으로
중복 정의하지 않고, framework를 제거할 필요가 있는지 실제 테스트·호출자 비용으로 판단한다. Rich domain,
CQRS/event sourcing은 복잡도를 상쇄할 근거가 있을 때 별도 선택한다.

## Worked example: report export

하나의 예로, 실제 요청이 **“권한이 있는 report를 CSV로 export한다”**라고 하자. 처음에는 이름 있는 operation과
기존 report reader/writer로 충분하다. 다음 표는 코드를 생성하라는 지시가 아니라 한 계약이 설계와 검증으로
이어지는 방식이다. API·CLI·UI는 실제 존재하는 consumer만 포함한다.

| 책임 | 구체적으로 기록/구현할 내용 | 보호할 assertion |
| --- | --- | --- |
| Spec | `docs/specs/report-export.md`에 허용 주체, CSV 결과, 빈 report와 failure 의미를 proposed로 정의 | 권한 없음은 write 없음; 빈 rows는 header-only CSV; write 실패는 성공 아님 |
| Use case | `export_report`/`exportReport`가 접근 확인, 읽기, render와 write를 조율 | 올바른 report/주체로 얻은 실제 export 결과와 오류 |
| Domain/policy | export 가능한 report 범위와 format 등 실제 invariant만 소유 | 거부 조건과 경계값; HTTP request나 storage client 없이 결정 검증 |
| Boundary | 실제 API/CLI의 입력·인증·error mapping 및 public field 보존 | malformed format/권한 오류가 선언된 status/exit/result로 매핑됨 |
| I/O seam | 외부 storage의 read/write와 stream 자원 수명은 그 collaborator가 소유 | adapter의 실제 temp-file/fake endpoint 동작, failure cleanup과 error 보존 |
| Consumer | 존재하는 UI/SDK/CLI가 결과와 오류를 해석 | public contract를 통한 성공·실패 경험; 내부 메서드 호출 횟수만 검사하지 않음 |

예를 들어 Python의 `test_export_report_without_access_does_not_write`,
`test_export_report_with_empty_rows_writes_header`, `test_export_report_when_write_fails_returns_error`는
spec의 서로 다른 조건을 드러내는 이름이다. 다른 언어도 같은 행동 경계를 해당 native test 관례로 표현한다.
Write를 하지 않는다는 side-effect assertion은 권한 거부의 중요한 계약이며, 성공 테스트는 실제 출력 내용도 확인한다.

**언제 port인가?** Storage가 실제 외부 I/O이므로 concrete writer를 주입해 정책 테스트와 I/O 검증을 분리할
이유가 있다. 기존 collaborator로 충분하면 ABC/trait를 새로 만들지 않는다. 교체 가능한 여러 storage나 안정된
외부 계약이 필요해질 때 지원할 메서드·error·cleanup 계약을 좁게 명시한다. Fake 통과만으로 실제 adapter를
검증했다고 하지 않는다.

**언제 strategy인가?** CSV만 필요할 때는 `render_csv` 함수면 된다. 실제 JSON export 요청이 추가되고 같은
입력/결과 계약에서 format별 동작이 변하면 callable 또는 작은 mapping으로 renderer를 선택할 수 있다.
기존 CSV regression을 보존하고 JSON 결과·unknown format·failure 테스트를 더한다. 미래 포맷을 위한 registry,
factory hierarchy 또는 class를 미리 만들지 않는다.

**어떻게 확장·변경하는가?** `output_format` 같은 public field를 바꾸면 wire schema의 권위와 모든 실제
producer/consumer, export 목록, fixtures, migration과 native checks를 함께 갱신한다. 구현·검증 뒤 spec을
current로 동기화한다. Domain, API, storage를 동시에 바꿔야 하는 반복 수정이 보이면 먼저 책임 누출과 중복된
계약 권위를 조사한다. 비슷한 파일 모양만으로 aggregate나 공유 framework를 만들지는 않는다.

## Optional robotics example: intent에서 관측 결과까지

Robotics capability를 선택한 프로젝트에서도 architecture의 목적은 같은 책임 분리다. 다음은 **설계 예시**이며
실제 robot runtime, navigation, actuator control이 template에 구현됐다는 뜻이 아니다. 기존 report-export 사례를
대체하는 보편 규칙도 아니다. 장치 I/O가 범위일 때 별도로 선택한 `robotics:robotics-software`와 그 번들의 공유 reference에서 상세 기준을 읽는다.
선택하지 않은 프로젝트에는 그 파일이 없으며 SDK나 transport를 가져올 필요도 없다.

예를 들어 “지정한 위치로 이동” intent가 생기면 다음 계약을 구분한다. 폴더나 class를 단계마다 만들라는 명령은 아니다.

| 경계 | 한 권위가 소유할 내용 | Software-only 검증 예 |
| --- | --- | --- |
| Intent | 목표·요청 identity·deadline·취소 의미 | malformed/expired 요청이 실행 경계에 도달하지 않음 |
| Admission | 허용 capability·현재 상태·권한·자원 한도 | 금지 상태/초과 요청은 거부하고 I/O 없음 |
| Control authority | 현재 owner·세대·우선순위·cancel/safe-state | 오래된 owner/완료 event가 새 작업을 덮어쓰지 않음 |
| Adapter | 실제 transport 변환·bounded I/O·정리 | timeout·부분 시작 실패·cancel 후 자원 정리; fake endpoint 사용 |
| Observed result | 실제 관측한 상태·상관 identity·실패/불명 구분 | queued/ACK만으로 목표 도달 성공을 보고하지 않음 |
| UI/API consumer | 요청 상태와 관측 결과의 구분·stale/error 표시 | 지연/실패/취소를 완료로 표시하지 않음 |

HTTP handler나 UI가 별도의 actuator authority를 만들지 않는다. Safety authority는 실제 프로젝트가 정한 위치에
유지하며, transport 연결·메시지 publish·build/test는 물리 동작 성공이 아니다. Fake 기반 admission/owner/cancel 회귀를
먼저 만들고 실기 검증은 명시적인 별도 승인과 증거로 분리한다. Shared schema를 바꾸면 모든 active consumer와
units/errors/version, 각 native package tests를 함께 갱신한다.

Python robot worker가 HTTP를 쓰지 않으면 기본 Python으로 충분하다. FastAPI는 실제 HTTP boundary가 필요할 때 추가한다.
Rust/C++ adapter, React operator UI도 필요한 component일 때만 조합한다. ROS/Dora/Zenoh/PyO3/FFI는 선택 capability의
자동 의존성이 아니며 실제 인터페이스와 lifecycle 요구를 확인한 뒤 별도로 결정한다.

## Frontend: feature와 state ownership

React 선택지는 `app -> features -> shared` 방향을 출발점으로 삼는다. `app`은 앱 조합, `features`는 사용자
행동, `shared`는 여러 실제 consumer가 쓰는 공통 UI/기능을 맡는다. Feature 간 연결이 필요하면 무조건
상호 import하기보다 상위 composition 또는 실제 공유 책임을 검토한다.

State는 가능한 가까운 단일 권위에 두고 derived state를 중복 보관하지 않는다. 서버의 원본 상태,
사용자 입력, loading/error/stale 표시와 도메인 결정은 구분한다. `useTransition`, memoization 또는 provider
도입은 network cancellation이나 business authority를 대신하지 않는다. 실제 React/framework version에서
지원하는 API만 사용하고, 시각 작업은 적용되는 design brief와 accessibility를 보존한다.

## Monorepo와 cross-language 계약

Monorepo는 협업 단위이지 하나의 runtime, dependency graph 또는 release 단위라는 뜻이 아니다.

| 경계 | 반드시 명시할 결정 |
| --- | --- |
| Python package/workspace | import 이름, `src/` packaging, interpreter, manifest/lock와 native checks |
| TypeScript library/service/browser | consumer runtime, ESM/CJS, compiler/bundler resolution, exports/types와 tests |
| Rust crate/workspace | library/bin target, public API, features/targets, toolchain/lock 정책과 native checks |
| Shared schema/event/API | canonical source, producer/consumers, units/errors/version/migration과 compatibility |
| Native/FFI | 실제 binding/ABI 또는 CLI/transport 방식, ownership/errors, packaging과 양쪽 검증 |

`paths` alias는 TypeScript package boundary나 emitted import rewrite가 아니다. `contracts/schemas` 폴더가
있다고 schema 언어, code generation 또는 domain authority가 정해진 것도 아니다. Rust crate와 Python
package를 나란히 놓아도 PyO3/Tokio/FFI가 자동으로 존재하지 않는다.

변경은 한 integration owner가 schema, producer, 모든 active consumer, fixture와 각 native 환경을 함께
추적한다. 외부 consumer가 없거나 검증 불가하면 그 한계를 남긴다. 동일 fixture의 byte 일치는 executed
interoperability가 아니며, 다른 언어의 test 통과만으로 native compatibility를 주장하지 않는다.
실행할 때는 .agents routing (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative)에서 실제 변경 경계에 맞는 contract/native skill을 선택한다.

## 분리하면서 지켜야 할 것

Timeout/retry/idempotency, partial-startup cleanup, task cancellation, shutdown, untrusted input validation과
safety authority는 구조 변경 과정에서 없어지면 안 된다. Abstract layer나 log/ACK를 추가했다고 이 성질이
검증된 것은 아니다. 실제 regression과 별도 review로 확인하며 deployment/hardware는 별도 증거로 보고한다.
