# Task brief: <outcome>

기존 프로젝트 양식과 저장 위치를 우선하며, 필요한 handoff가 있을 때만 해당 항목을 채운다.

## Outcome와 소유 범위

- 관찰 가능한 완료 조건:
- owning package/files 및 integration owner:
- 영향받는 호출자/계약/consumers:
- exclusions와 허용된 side effects:
- 대표 use case와 지킬 invariant; 실제 책임·I/O/variant seam:

## 읽을 정확한 안내

- 적용되는 `AGENTS.md`와 package README:
- 필요한 조직 plugin/task `SKILL.md` entrypoint와 그 작업에 적용할 구체적 제약:
- native environment/toolchain/manifest/lockfile 및 safety/lifecycle 권위:
- firmware이면 선택한 board/environment와 electrical/calibration·non-actuating 제한:

역할명만 적는 것은 skill 선택 근거가 아니다. 해당 없는 skill은 추가하지 않는다.

## Evidence와 handoff

- 변경 전 확인할 caller/tests/fixtures/config/exports:
- behavioral regression / characterization / static evidence 중 선택:
- 기존/신규 variant와 public contract의 success/error/lifecycle assertions:
- focused checks와 실제 package completion gates, 또는 execution 제외:
- compatibility, rollback 및 외부 검증 한계:
- 독립 review가 필요한 경계와 reviewer가 확인할 구체적 실패 조건:

병렬 작업이면 다른 작업자가 있음을 알리고 공유 파일은 integration owner에게 맡긴다. 타인의 변경을 되돌리지
않고 충돌/차단 원인을 보고한다. 자식 작업은 별도 허가 없이 다시 orchestration하지 않는다.
완료 시 변경 파일, 실제 관찰한 check 결과, 누락/위험과 rollback을 보고한다.
