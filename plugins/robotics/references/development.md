# 개발 workflow

이 문서는 설치된 common plugin의 공유 개발 기준이다. 프로젝트마다 같은 지침을 복사하지 않는다. 현재 package, 제공 기능과 실제
명령은 프로젝트 README (look up `README.md` in the consuming repository; its current project guidance remains authoritative)를 기준으로 확인한다. 작업별 shared skill과 common plugin의
naming·설계·review resource는 .agents routing (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative)을 통해 찾는다.
문서가 있다는 사실은 실행 또는 LLM 준수의 증거가 아니다.

## 작업을 먼저 분류한다

| 작업 | 작은 완료 경계 | 증거 |
| --- | --- | --- |
| 조사/review | source, callers와 계약을 확인하고 결론/불확실성 분리 | 구체적 경로, 실패 조건과 근거; 불필요한 수정 없음 |
| 문서/skill/skeleton | 요청한 파일과 참조를 함께 갱신 | metadata, local links, provenance/licenses, 전체 파일·whitespace 검토 |
| 행동 변경/bug fix | 기대 행동 → 실제 failing assertion → 최소 수정 | focused regression 및 owning package gate |
| 행동 보존 refactor | 기존 행동 characterization → 추출 | error, branch priority, lifecycle과 integration coverage 보존 |
| 공유 계약/concurrency/safety | 짧은 spec, 소유자·consumer·환경 지도 | 각 native gate, 경계 사례와 별도 review |
| Generator·manifest·실행 automation | 실제 입력/출력과 native 환경 계약 | 생성 결과의 동작/오류·consumer 검증; prose-only 예외 적용 안 됨 |

Runtime/build/deployment/CI 설정은 문서가 아니라 application 검증 범위다. 반대로 문서만 고친 작업을 위해
앱을 설치하거나 서비스·CI·hardware를 실행하지 않는다. 명확히 허가된 작업은 같은 승인을 다시 묻지 않고
완료한다. commit, publish, 외부 상태 변경과 live/hardware 접근은 작업 권한을 따로 확인한다.

## SDD, TDD, 선택적 DDD

**SDD — specification-driven development:** 의미 있는 행동/호환성 변경에서 outcome, invariants와 acceptance를
먼저 명확히 한다. Spec의 입력·결과·실패 의미가 테스트에서 관찰 가능해야 한다. 작은 수정은 충분한
issue/task brief로 끝내고, 여러 package나 protocol을 조율할 때
change spec (shared skill `common:spec-driven-development`; select the `common` bundle when that task boundary is in scope)을 쓴다. 유지되는 계약은 specs (look up `docs/specs/README.md` in the consuming repository; its current project guidance remains authoritative)에 두며
proposed/implementing/current/superseded 상태를 구분한다. 검증 후 실제 계약을 동기화하며 미구현 의도를 현재
지원으로 표시하지 않는다. Spec Kit/OpenSpec 설치와 모든 작업의 문서 의식은 요구하지 않는다.

**TDD — test-driven development:** 새 행동/bug fix는 해당 행동의 assertion이 실패하는 것을 확인한 뒤
구현한다. import 실패나 깨진 fixture는 버그 재현이 아니다. 보존할 행동은 characterization, prose는 static
check를 사용한다. 형식상 RED를 만들려고 문서를 위해 application test를 실행하지 않는다. 이미 구현이 먼저
있다면 안전한 baseline 재현이 가능한지 확인하고 증거 공백을 솔직히 적는다. 타인의 구현을 삭제해 RED를
만들거나 관찰하지 않은 과거 RED를 주장하지 않는다.

**DDD — domain-driven design:** 상태 소유권, 용어, 불변조건과 변경 이유가 실제로 복잡한 곳에 선택한다.
작은 CRUD/service에 aggregate, repository interface, CQRS와 event sourcing을 일괄 추가하지 않는다.
DTO 공유와 business authority 공유는 다르다. 하나의 export use case를 spec·invariant·test·실제 I/O seam에
연결한 [worked example](architecture.md#worked-example-report-export)에서 적용 단위를 볼 수 있다.

## 구현 전후의 짧은 루프

1. 범위, 소유 package/files, 호출자·consumer, 제외 사항과 acceptance를 적는다. Import/export, fixtures,
   config, generated source와 native environment까지 영향 범위를 찾는다.
2. 현재 코드/계약과 해당 shared skill만 읽고, 적용할 구체적 제약을 짧게 남긴다. 결함이면 같은 mechanism의
   형제 호출자와 공통 원인도 확인하고, 근거가 있는 가장 작은 공통 원인을 고친다.
3. 변경 종류에 맞는 regression/characterization/static evidence를 준비하고 가장 작은 완전한 수정을 한다.
   하나의 public 행동에서 success뿐 아니라 해당 경계의 invalid input·failure·cleanup을 검증한다.
4. 실제 package 환경에서 focused checks와 선언된 completion gate를 수행한다. 공통 root 명령이 있더라도
   package-native gate의 소유권과 언어별 compatibility evidence를 생략하지 않는다.
5. 중요한 contract/concurrency/safety 변경은 별도 reviewer가 실패 조건과 증거를 검토한다. 같은 작성자의
   self-check를 독립 review라고 부르지 않는다.
6. README/current specs를 실제 결과와 맞추고, 변경 경계·관찰된 check·생략·위험·rollback을 보고한다.

서로 독립적인 작업은 명확한 file ownership으로 병렬화할 수 있다. 공유 schema/공유 문서 수정과 dependent
작업은 integration owner가 조율한다. 다른 작업자의 변경을 되돌리지 않는다.
Task brief template (shared skill `common:writing-plans`; select the `common` bundle when that task boundary is in scope)을 필요한 handoff에만 사용한다.

## 테스트와 확장 시 확인

- 테스트는 Arrange–Act–Assert로 실제 결과·상태·오류를 확인한다. Mock 호출 횟수만으로 성공을 증명하지 않는다.
  시간·random·외부 I/O는 좁은 collaborator나 기존 fixture로 제어하고 각 테스트가 소유한 자원을 정리한다.
- Pure policy는 빠른 unit test, 실제 storage/transport 동작은 adapter/integration test, 사용자/consumer 계약은
  API/CLI/UI/package-boundary test로 확인한다. 모든 테스트에 DB나 전체 service stack을 요구하지 않는다.
- 새 strategy/adapter를 추가할 때 기존 public contract의 success/error/lifecycle 테스트를 재사용하고 새 구현의
  차이만 추가한다. 새 wire field/export이면 producer·consumer·fixtures·docs와 구버전 호환 경로를 함께 확인한다.
- Shared-state, deadline, cancellation, partial startup과 cleanup이 변경되면 그 실패 사례를 추가한다. Coverage
  비율이나 test 개수는 assertion 품질의 대체가 아니며 근거 없이 새로운 threshold를 강제하지 않는다.

## Native 환경과 실제 gate

선언된 runtime/toolchain, manifest·lockfile와 check 명령은 해당 package가 소유한다. 없다면 구현 범위에서
지원 환경을 정하고 pin한 뒤 실제 gate를 추가한다. Python package에 Node/React 설정을 섞거나 firmware를
Python application으로 취급하지 않는다. Firmware이면 실제 board/environment와 안전 경계를 따로 확인한다.
예시가 쓰는 최신 버전에 맞추기 위한 업그레이드나 ad-hoc 설치를 검증 근거로 삼지 않는다.

Iteration 중에는 focused checks, 완료 시에는 선언된 package/repository gate를 실행한다. Root orchestration은
각 언어의 native 검증을 대체하지 않는다. 다른 실패도 관찰했다면 원인·영향을 보고하며 조용히 제외하지 않는다.
명령이 없거나 실행이 제외되었다면 통과 결과를 만들지 말고 필요한 검증과 미수행 이유를 남긴다.

검증 결과는 **static / software-tested / deployed / physically validated**를 구분한다. Skill 파일·role 설정의
존재는 fresh-session discovery, 자동 선택 또는 model adherence의 증거가 아니다.

## Source-first development

기존 source·callers·tests·manifest·lock과 실제 실행 계약을 먼저 확인하고 사실과 제안을 구분한다.
관찰한 계약과 변경 이유 → 명세·acceptance → 행동 테스트 → 최소 구현 → 소비자 확인으로 연결한다.
여기서 source-first는 작업 원칙이며 별도 표준 방법론이나 SDD의 다른 정의로 주장하지 않는다.
SDD는 위에서 정의한 specification-driven development를 뜻한다.

## Reference approaches

- [Spec Kit existing projects](https://github.com/github/spec-kit/blob/main/docs/guides/existing-projects.md): 기존 프로젝트의 규칙과 현재 구현을 보존하면서 명세를 적용한다.
- [OpenSpec concepts](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md): 유지 계약과 변경 의도를 구분한다.

참고 접근법이며 CLI 설치, 새 형식 또는 승인 의식을 요구하지 않는다.
