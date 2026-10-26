# Canonical skill task pointers

[Maintainer contract](../../AGENTS.md)와 현재 요청, 변경 소유자를 먼저 확인합니다. 이 경로는 공통 원본입니다.
호스트에는 생성된 plugin을 설치하며 `project-blueprints`에는 스킬 본문이나 원본 목록을 복제하지 않습니다.
Plugin 소유권은 [catalog](../../catalog.json), 원본·수정 hash는 [manifest](skill-sources.json)가 관리합니다.

## Required skill selection and evidence

1. 실제 작업에 해당하는 정확한 entrypoint만 읽고 상세 reference는 해당 branch에서 읽습니다.
2. 기존 프로젝트의 AGENTS·package manifest·lock·명령·안전 계약이 예시보다 우선합니다.
3. 어떤 기준이 결정에 영향을 주었는지 설명합니다. 파일 존재, 설치, 새 세션 발견, 호출, 준수는 별개입니다.
4. 독립 업무에는 소유 파일·정확한 지침·검증 기준을 주며 타인 변경을 보존합니다.
5. 동작 변경은 regression, 보존은 characterization, 문서는 static checks로 검증합니다.

## Task pointers

| 작업/경계 | 정확한 local entrypoint |
| --- | --- |
| API·wire contract·오류 의미의 설계/리뷰 | [api-design-principles](skills/api-design-principles/SKILL.md) |
| 책임·SRP·계층·DDD·의존 방향을 선택/변경 | [architecture-patterns](skills/architecture-patterns/SKILL.md) |
| 실제 Python async 변경; cancellation·deadline·backpressure | [async-python-patterns](skills/async-python-patterns/SKILL.md) |
| 현재 권장사항·외부 구현 조사; official/upstream 근거 우선 | [best-practice-research](skills/best-practice-research/SKILL.md) |
| 아직 결정되지 않은 요구·설계의 선택지 비교 | [brainstorming](skills/brainstorming/SKILL.md) |
| 독립 코드 리뷰; 위치·실패 조건·심각도·최소 수정 | [code-review-excellence](skills/code-review-excellence/SKILL.md) |
| 응집된 모듈·인터페이스·test seam·공통화·확장성 판단 | [codebase-design](skills/codebase-design/SKILL.md) |
| 공개 이름/API 제거·호환성 이행; 외부 consumer 확인 | [deprecation-and-migration](skills/deprecation-and-migration/SKILL.md) |
| 도메인 용어·소유권·불변식·기존 glossary/ADR 정리 | [domain-modeling](skills/domain-modeling/SKILL.md) |
| 현재 코드/명세/README/agent 지침의 일치 여부 | [docs-sync](skills/docs-sync/SKILL.md) |
| 선택한 MCU/toolchain의 firmware timing·ISR·RTOS·resource bounds | [embedded-systems](skills/embedded-systems/SKILL.md) |
| FastAPI app/router·입력 검증·dependency/lifespan·HTTP 경계 변경 | [fastapi-backend](skills/fastapi-backend/SKILL.md) |
| 승인된 시각 UI 생성/재설계; 먼저 DESIGN.md | [frontend-design](skills/frontend-design/SKILL.md) |
| 요청된 UI audit·polish·loading/error/a11y hardening | [impeccable](skills/impeccable/SKILL.md) |
| Litestar handler/router·명시적 DI·lifecycle·HTTP 경계 변경 | [litestar-backend](skills/litestar-backend/SKILL.md) |
| C++ ownership·RAII·비소유 lifetime·bounds·allocation/failure | [memory-safety-patterns](skills/memory-safety-patterns/SKILL.md) |
| 여러 package/언어에 걸친 schema·producer/consumer 변경 | [monorepo-contract-change](skills/monorepo-contract-change/SKILL.md) |
| NestJS modules/providers·DTO 검증·controller·HTTP lifecycle 변경 | [nestjs-backend](skills/nestjs-backend/SKILL.md) |
| Next.js App Router·server/client·Route Handler/Action·캐시 경계 변경 | [nextjs-app-router](skills/nextjs-app-router/SKILL.md) |
| 실측 진단 공백·요청된 logs/metrics/traces; redaction·bounded cardinality | [observability-and-instrumentation](skills/observability-and-instrumentation/SKILL.md) |
| 구현·리팩터링·의존성/추상화 추가 전 최소 완전한 해법 | [ponytail](skills/ponytail/SKILL.md) |
| Python SRP·KISS·composition·구체적 collaborator·선택적 pattern | [python-design-patterns](skills/python-design-patterns/SKILL.md) |
| 입력 검증·예외 의미·부분 실패·호출 경계 | [python-error-handling](skills/python-error-handling/SKILL.md) |
| Python import·src layout·public API·packaging 경계 | [python-project-structure](skills/python-project-structure/SKILL.md) |
| connections/files/task의 소유권·부분 시작·정리 실패 | [python-resource-management](skills/python-resource-management/SKILL.md) |
| Python annotations·generics·Protocol·기존 checker의 버전과 경계 | [python-type-safety](skills/python-type-safety/SKILL.md) |
| pytest fixtures·테스트 경계·실제 오류/불변식 회귀 | [python-testing-patterns](skills/python-testing-patterns/SKILL.md) |
| 로봇·장치의 단위/좌표/시간·명령/안전 소유권·stale data·비작동 검증 | [robotics-software](skills/robotics-software/SKILL.md) |
| 명시적으로 선택된 Rust async의 task ownership·shutdown·backpressure | [rust-async-patterns](skills/rust-async-patterns/SKILL.md) |
| Rust ownership·Result·visibility·traits·native checks | [rust-best-practices](skills/rust-best-practices/SKILL.md) |
| trust boundary·auth·민감 데이터·untrusted input | [security-and-hardening](skills/security-and-hardening/SKILL.md) |
| 의미 있는 동작/호환성 변경의 수용 기준·명세 동기화 | [spec-driven-development](skills/spec-driven-development/SKILL.md) |
| 결함 재현·callers/계약/형제 모듈에서 공통 원인 추적 | [systematic-debugging](skills/systematic-debugging/SKILL.md) |
| 변경 동작은 RED/GREEN, 보존은 characterization, 문서는 static | [test-driven-development](skills/test-driven-development/SKILL.md) |
| Node/browser·ESM·exports·strict types·실제 import graph | [typescript-project-structure](skills/typescript-project-structure/SKILL.md) |
| React component API·composition·state ownership 변경 | [vercel-composition-patterns](skills/vercel-composition-patterns/SKILL.md) |
| 선택한 React/framework 버전의 rendering·data·성능 변경 | [vercel-react-best-practices](skills/vercel-react-best-practices/SKILL.md) |
| 완료 주장 직전 실제 범위의 명령·출력·누락 확인 | [verification-before-completion](skills/verification-before-completion/SKILL.md) |
| UI interaction·keyboard/focus·semantic·접근성 리뷰 | [web-design-guidelines](skills/web-design-guidelines/SKILL.md) |
| skill·AGENTS·조건부 routing 설계; progressive disclosure | [writing-for-agents](skills/writing-for-agents/SKILL.md) |
| 확정된 다단계 요구의 소유 파일·인터페이스·검증 분할 | [writing-plans](skills/writing-plans/SKILL.md) |

[Engineering criteria](references/engineering.md)가 SRP·KISS·naming·의존 방향의 공통 기준입니다.
작업 방법과 검증 경계를 정할 때는 [development](references/development.md), 실제 설계 판단에는
[architecture example](references/architecture.md), 장치 I/O의 Python/API/UI 경계에는
[robotics example](references/robotics.md)을 해당 작업에서만 읽습니다. 이 공통 지침은 프로젝트에 복사하지 않습니다.
Rust 변경은 [Rust 기준](references/rust.md), 펌웨어 변경은 [firmware 기준](references/cpp-firmware.md)을 확인합니다.
실제 버전·runtime·toolchain·board는 소비 프로젝트가 소유합니다. 예시는 설치·배포·실기 권한이 아닙니다.

## Roles and maintenance

공통 역할은 [architect](../agents/architect.toml), [executor](../agents/executor.toml),
[code-reviewer](../agents/code-reviewer.toml), [verifier](../agents/verifier.toml)의 한 원본에서 생성합니다.
모든 작업에 네 역할을 강제하지 않습니다. [Host 지원](../../docs/hosts.md#optional-hooks-and-native-agents)을 확인합니다.
Claude native adapter와 Codex 명시적 export를 자동 등록으로 혼동하지 않습니다.

원본을 바꾸면 immutable upstream 기록과 검토한 local hash를 함께 유지하고 plugin을 재생성합니다.
[검증·릴리스·호스트 갱신](../../docs/releases.md)은 template의 구조 업데이트와 별개입니다.
명확한 승인 범위는 반복해서 묻지 않으며 커밋·게시·배포·실기는 각각 실제 권한이 필요합니다.
