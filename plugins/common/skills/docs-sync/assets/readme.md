# README: <package-or-folder-name>

기존 README와 프로젝트 관례를 우선한다. 새 package/folder의 책임이나 사용 계약이 불명확할 때만 필요한
항목을 남겨 채운다. 단순 폴더는 짧은 책임 설명과 상위 문서 링크면 충분하다. 모든 폴더에 양식을 복제하지 않는다.
Agent 제약은 적용되는 `AGENTS.md`, 작업 절차는 선택한 skill로 연결하고 여기 복제하지 않는다.

## 목적과 상태

- 책임과 주요 사용자/호출자:
- 상태: skeleton / implemented / deprecated
- 포함할 항목과 하지 않는 일:

## 경계와 공개 표면

- 주요 하위 경로와 책임, 권위 있는 소유자:
- 실제 entrypoint / public exports / API와 비공개 구현:
- 허용 의존 방향, 외부 시스템과 권위 있는 schema 및 producer/consumer:
- 대표 use case, 상태 소유자와 보존할 invariant:
- 실제 extension seam이 있으면 collaborator/strategy 계약과 오류·lifecycle 의미:

실제 언어/tool의 native layout을 설명한다. 저장소가 단일 package인지 monorepo인지 확인하고 분류 경로를
추측하지 않는다. 선택하지 않은 framework/DDD layer, 별도 interface나 가상의 확장점을 채우지 않는다.

## 환경과 사용 — 실행 가능한 package에만

- runtime/toolchain, manifest와 lockfile 소유 위치:
- 실제 존재하는 설치/실행 명령과 실행 디렉터리:
- 필요한 설정, 비밀정보 취급 및 lifecycle:
- firmware인 경우에만 board/environment, electrical/calibration profile과 non-actuating/safe-state 경계:

Skeleton 단계라면 실행 명령을 상상해 넣지 말고 미구현 결정을 적는다. 빈 디렉터리가 실제로 필요하고
설명할 책임이 없을 때만 `.gitkeep`를 사용한다. README가 이미 추적하면 중복 표식을 넣지 않는다.

## 검증과 호환성 — 바뀌는 경계에만

- 영향받는 import/export/schema, tests/docs와 실제 검증 위치:
- 실제 존재하는 test/typecheck/lint/build 명령과 적용 native 환경:
- public behavior, policy, adapter/native integration과 consumer 검증의 위치:
- 지원 범위, error/compatibility 계약 및 알려진 한계:
- 새 variant/adapter/export 추가 시 보존할 contract tests와 consumer 변경 절차:
- 배포 또는 hardware 검증이 필요한 경우 별도 승인과 증거:

명령·파일 존재와 실제 통과 결과를 구분한다. 예시 테스트나 fake 통과를 production I/O 검증으로 보고하지 않는다.

## 관련 문서

유지되는 spec/ADR, 사용 예제와 상위 문서의 실제 상대 링크를 추가한다. 같은 규칙이나 날짜별 세션 로그는 복제하지 않는다.
