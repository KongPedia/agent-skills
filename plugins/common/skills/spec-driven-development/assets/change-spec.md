# Change specification: <observable outcome>

기존 프로젝트 양식과 저장 위치를 우선한다. 명확한 issue/task brief가 충분하면 중복 생성하지 않는다. 유지할 계약은 `docs/specs/`, 임시 계획은 ignored
`.omx/plans/`에 둔다. 아래 항목 중 해당 없는 것은 이유를 적거나 제거한다.

## 상태와 계약 권위

- 상태: proposed / implementing / current / superseded
- 소유자 및 현재 계약/대체 spec 링크:
- 구현·검증 근거와 미검증 범위:

## Outcome와 범위

- 관찰 가능한 결과와 acceptance criteria:
- in scope / out of scope:
- owning packages 및 producer/consumer, 외부 handoff:
- 각 native runtime/toolchain, manifest, lockfile 및 schema 권위:

## Use case와 invariant

| 입력·주체·상태 | 기대 결과 또는 거부 조건 | invariant/오류 의미 | 보호할 behavioral assertion |
| --- | --- | --- | --- |
| <scenario> | <observable outcome> | <constraint> | <test boundary> |

작은 작업은 충분한 acceptance 항목으로 이 표를 대신할 수 있다. 실제로 나뉘는 boundary/use case/policy/I/O의
책임을 적되 폴더·class를 강제하지 않는다. Port/strategy가 필요하면 실제 외부 I/O나 variant, public 계약과
failure/lifecycle 의미를 적는다. 앞으로 생길 가상의 구현을 위해 interface를 만들지 않는다.

## Consumer와 native 환경

| Producer/consumer | 계약 원본·public surface | manifest/lock·환경·gate | 변경/호환성·외부 handoff |
| --- | --- | --- | --- |
| <owner> | <authority> | <native checks> | <migration or unavailable evidence> |

해당 없는 언어·배포 단위는 추가하지 않는다. Firmware이면 선택한 board/environment와 electrical/calibration 및
safety authority를 함께 기록한다. 다른 언어가 같은 저장소에 있다는 이유로 FFI나 공통 lock을 가정하지 않는다.

## 보존할 계약과 migration

- API/export/schema, identity/units/error/order/lifecycle 호환성:
- 변경하지 않을 데이터·보안·안전 경계:
- migration 순서와 기존/신규 버전 공존 조건:
- generated/vendor 영역의 원본 및 편집 경계:
- 실제 strategy/adapter를 확장할 때 기존/신규 variant의 contract tests:

## Verification

| Acceptance criterion | 검증 계층·환경·실제 명령/자료 | 예상 결과 | 관찰 결과·한계 |
| --- | --- | --- | --- |
| <criterion> | <evidence> | <expected> | <observed or not run> |

새 행동/수정은 behavioral failing regression, 보존은 characterization, 문서/skeleton은 static checks를 선택한다.
실제 application gate는 owning package에서 정하며 이 template은 가상의 통과 명령을 제공하지 않는다.
공유 계약은 모든 active consumer와 별도 review를 포함한다. software/deployment/physical evidence를 구분한다.
Unit policy와 실제 adapter/integration evidence를 구분하고, 바뀐 경계의 invalid input, failure, deadline/cancel과
cleanup 사례를 포함한다. 이미 존재한 구현의 RED를 관찰하지 않았다면 그 공백을 숨기지 않는다.

## Rollback와 동기화

- 데이터·호출자·안전 상태를 보존하는 rollback:
- 검증 후 갱신할 current specs/README/ADR:
- 남은 proposal 및 외부 호환성 handoff:

명확히 허가된 작업은 재승인 절차 없이 진행한다. release, publish, live/hardware 작업은 별도 권한이다.
