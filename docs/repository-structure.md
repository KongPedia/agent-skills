# 저장소·플러그인 구조 안내

이 저장소는 **`plugins/` 안의 원본을 직접 관리하고, 설치 가능한 패키지도 같은 위치에서 제공**합니다.
예전 `source/`와 루트 `hooks/`는 현재 구조에 없습니다. 스킬·훅·역할 원본을 없앤 것이 아니라 플러그인 소유 위치로 통합했습니다.
전체 스킬의 진입점과 사용 조건은 [스킬 카탈로그](skill-catalog.md), 설치·신뢰·갱신 절차는 [호스트 안내](hosts.md)를 확인하세요.

## 훅과 역할 TOML은 어디에 있나요?

| 내용 | 현재 위치 | 수정 여부 |
| --- | --- | --- |
| 선택형 SessionStart 훅 원본 | [`plugins/session-guidance/hooks/session-start.sh`](../plugins/session-guidance/hooks/session-start.sh) | 원본 수정 |
| 훅 실행 설정 | [`plugins/session-guidance/hooks/hooks.json`](../plugins/session-guidance/hooks/hooks.json) | 생성물; 직접 수정하지 않음 |
| Architect 역할 원본 | [`plugins/common/exports/codex/agents/architect.toml`](../plugins/common/exports/codex/agents/architect.toml) | 원본 수정 |
| Code reviewer 역할 원본 | [`plugins/common/exports/codex/agents/code-reviewer.toml`](../plugins/common/exports/codex/agents/code-reviewer.toml) | 원본 수정 |
| Executor 역할 원본 | [`plugins/common/exports/codex/agents/executor.toml`](../plugins/common/exports/codex/agents/executor.toml) | 원본 수정 |
| Verifier 역할 원본 | [`plugins/common/exports/codex/agents/verifier.toml`](../plugins/common/exports/codex/agents/verifier.toml) | 원본 수정 |
| Claude 역할 어댑터 4개 | [`plugins/common/agents/`](../plugins/common/agents/) | 위 TOML에서 생성; 직접 수정하지 않음 |

`exports/`라는 이름과 달리 **현재 네 TOML의 작성 원본은 이 경로**입니다. 별도의 `source/agents/`는 없습니다.
다만 패키지에 포함된 TOML은 명시적으로 프로비저닝할 수 있는 자료이지, Codex 플러그인 설치만으로 자동 등록되는 역할이 아닙니다.
소비 프로젝트의 `.codex/agents/`와 사용자 호스트 설정은 이 저장소의 원본과 별개입니다.
루트 [`pyproject.toml`](../pyproject.toml)은 저장소 Python 도구 설정으로, 역할 TOML과 다른 파일입니다.

`session-guidance`는 별도 선택하는 플러그인입니다. 훅은 고정된 안내문을 `printf`로 출력하며,
저장소 스캔·네트워크·테스트·애플리케이션 실행·권한 변경·하드웨어 조작을 하지 않습니다.
플러그인 설치/활성화와 훅 신뢰 승인은 별개이며, 설치가 자동 신뢰를 뜻하지 않습니다.
훅 설정은 기본 `hooks/hooks.json` 탐색을 사용합니다. 클라이언트별 지원 경계는 [훅과 native agents](hosts.md#optional-hooks-and-native-agents)에 있습니다.

## 폴더 지도

아래는 관리에 필요한 경로만 추린 구조입니다. `<bundle>`, `<skill>`, `<owner>`는 자리표시자입니다.
`원본`은 직접 관리하는 입력, `생성`은 준비 스크립트가 원본에서 만드는 파일을 뜻합니다.

```text
agent-skills/
├── AGENTS.md                         # 저장소 유지보수 계약
├── README.md                         # 시작점
├── catalog.json                      # 원본: 번들 ID·버전·스킬 소유권·조합
├── provenance/
│   └── skill-sources.json            # 원본: v2 출처·원본 경로·검토한 해시
├── plugins/
│   ├── <bundle>/
│   │   ├── skills/<skill>/           # 원본: SKILL.md와 해당 스킬 자료
│   │   ├── references/               # 소유 원본 또는 생성된 패키지용 사본
│   │   ├── licenses/                 # 소유 원본 또는 생성된 라이선스/NOTICE 사본
│   │   ├── plugin.json               # 생성: portable 플러그인 manifest
│   │   ├── .claude-plugin/plugin.json # 생성: Claude manifest
│   │   ├── provenance.json           # 생성: 이 패키지 파일의 출처/변환
│   │   ├── artifact-hashes.json      # 생성: 패키지 파일 해시
│   │   ├── DEPENDENCIES.md           # 생성: 명시적 번들 선택 안내
│   │   └── THIRD-PARTY-NOTICES.md     # 생성: 선택된 외부 자료 안내
│   ├── common/
│   │   ├── exports/codex/agents/      # 원본: 역할 TOML 4개
│   │   └── agents/                   # 생성: Claude 역할 Markdown 4개
│   └── session-guidance/hooks/
│       ├── session-start.sh          # 원본: 선택형 안내 훅
│       └── hooks.json                # 생성: SessionStart 실행 설정
├── .agents/plugins/marketplace.json  # 생성: Codex 플러그인 인덱스
├── .claude-plugin/marketplace.json    # 생성: Claude 플러그인 인덱스
├── scripts/                          # 패키지 준비·선택형 평가 도구
├── tests/                            # 유지보수 도구/패키지 검증
├── evals/                            # 선택형 에이전트 행동 평가 자료
├── docs/                             # 사용자·유지보수 문서
├── pyproject.toml                    # Python 유지보수 도구 설정
└── uv.lock                           # 유지보수 의존성 잠금
```

이 지도는 모든 번들이 `skills/`, `references/`, `licenses/`를 가진다는 뜻이 아닙니다.
예를 들어 `session-guidance`에는 스킬이 없습니다. 실제 포함 파일은 해당 패키지와 출처 기록을 확인합니다.
`.venv/`, `.pytest_cache/`, `.omx/` 같은 로컬 실행 산출물은 스킬 작성 원본이 아닙니다.

## 스킬·번들·프로필·스캐폴드의 차이

| 단위 | 역할 | 소유 위치 |
| --- | --- | --- |
| 스킬 | 특정 작업의 절차와 필요한 자료; `SKILL.md`가 진입점 | `plugins/<bundle>/skills/<skill>/` |
| 번들 = 플러그인 | 함께 설치하는 배포 단위; 이 저장소에서는 같은 단위 | `plugins/<bundle>/` |
| Marketplace | 호스트가 플러그인 이름을 경로에 연결하는 인덱스; 별도의 스킬 원본 아님 | 루트의 두 marketplace JSON |
| 프로필 | React/Vite, FastAPI 등 프로젝트에 맞는 번들 선택 조합 | 별도 `project-blueprints` 저장소 |
| 스캐폴드 | Copier가 생성하는 프로젝트 초기 파일·설정·라우팅 | 별도 `project-blueprints` 저장소와 생성된 프로젝트 |

현재 [catalog.json](../catalog.json)의 구성은 **13개 번들, 42개 스킬**입니다.

| 번들 | 스킬 수 | 책임 | `requires` 조합 |
| --- | ---: | --- | --- |
| `common` | 18 | 공통 설계·개발 절차·검증·문서·보안 및 역할 자료 | 없음 |
| `python` | 7 | Python 구조·설계·오류·자원·비동기·타입·테스트 | 없음 |
| `typescript` | 1 | TypeScript 프로젝트/패키지 경계 | 없음 |
| `react-ui` | 6 | React 구성·성능과 시각 UI/UX 설계·리뷰 | `typescript` |
| `api-contracts` | 1 | 공유 API 설계 원칙 | 없음 |
| `fastapi` | 1 | FastAPI 구현·HTTP/lifecycle 경계 | `python`, `api-contracts` |
| `litestar` | 1 | Litestar 구현·DI/HTTP/lifecycle 경계 | `python`, `api-contracts` |
| `nestjs` | 1 | NestJS module/provider·HTTP 경계 | `typescript`, `api-contracts` |
| `nextjs` | 1 | Next.js App Router·server/client·캐시 경계 | `typescript`, `react-ui`, `api-contracts` |
| `rust` | 2 | Rust 기본 설계와 선택적 async 설계 | 없음 |
| `cpp-firmware` | 2 | Firmware와 C++ 메모리 안전성 | 없음 |
| `robotics` | 1 | 센서/명령 계약·시간·좌표·안전 소유권 | 없음 |
| `session-guidance` | 0 | 별도 선택하는 SessionStart 안내 훅 | 없음 |

`requires`는 조합을 설명하는 메타데이터입니다. 호스트가 의존 플러그인을 자동 설치한다는 스키마가 아닙니다.
전체 42개 스킬 목록과 사용 조건은 [스킬 카탈로그](skill-catalog.md) 한 곳에서 확인합니다.

### React UI와 UI UX Pro Max

`plugins/react-ui/skills/`에는 다음 여섯 스킬이 있습니다.

- `frontend-design`: 시각적 방향·타이포그래피·레이아웃 설계
- `ui-ux-pro-max`: 제품에 맞는 스타일·색상·타입·UI/UX 검색 자료
- `impeccable`: 기존 UI 비평·polish·상태와 접근성 보강
- `web-design-guidelines`: 인터랙션·키보드·focus·접근성 리뷰
- `vercel-composition-patterns`: React 컴포넌트 구성·API·상태 소유권
- `vercel-react-best-practices`: React/framework 렌더링·데이터·성능

UI UX Pro Max의 작성 원본은 **[`plugins/react-ui/skills/ui-ux-pro-max/`](../plugins/react-ui/skills/ui-ux-pro-max/) 하나**입니다.
`SKILL.md`, `scripts/`, `data/`, `references/`가 같은 스킬을 이룹니다.
설치 캐시에 생기는 사본은 두 번째 작성 원본이 아닙니다. 디자인 작업의 조합과 비시각적 수정의 제외 조건은
[프런트엔드 워크플로](frontend-workflows.md)를 따릅니다. 설치만으로 모든 작업에서 강제 호출되거나 디자인 품질이 보장되지는 않습니다.

## 무엇을 수정하고, 무엇을 재생성하나요?

| 바꾸려는 내용 | 수정할 원본 | 직접 수정하지 않을 대상 |
| --- | --- | --- |
| 스킬 절차·자료 | 해당 `plugins/<bundle>/skills/<skill>/` | 호스트 설치 캐시 |
| 공유 reference·라이선스/NOTICE | 중앙 출처 기록에 등록된 소유 플러그인의 파일 | 다른 번들의 패키지용 사본 |
| 공통 역할 | Common의 `exports/codex/agents/*.toml` | Common의 `agents/*.md` |
| 안내 훅 문구 | `plugins/session-guidance/hooks/session-start.sh` | 생성된 `hooks.json` |
| 번들 ID·버전·스킬 소유권·조합 | `catalog.json` | 두 marketplace 인덱스·플러그인 manifest |
| 출처·검토한 원본 해시 | `provenance/skill-sources.json` | 각 플러그인의 `provenance.json`, `artifact-hashes.json` |
| 생성 규칙 | `scripts/build_plugins.py`와 해당 회귀 테스트 | 개별 생성 결과의 수동 우회 수정 |

**`plugins/` 전체가 생성물도, 그 안의 모든 파일이 원본도 아닙니다.** 공유 자료는 중앙 출처 기록의 소유자를 기준으로 구분합니다.
공통 reference 원본은 `plugins/common/references/`, 도메인 reference 원본은 각각
`plugins/rust/references/`, `plugins/cpp-firmware/references/`, `plugins/robotics/references/`입니다.
독립적으로 설치되는 패키지에는 필요한 reference와 라이선스 사본이 포함될 수 있습니다.
이는 패키지를 닫힌 형태로 제공하기 위한 생성 사본이지, 두 곳에서 따로 수정할 스킬 원본이 아닙니다.

중앙 출처 기록의 필드는 서로 다른 사실을 뜻합니다.

- `local`: 이 저장소 기준의 현재 작성 원본 경로. Imported `files` 및 authored 항목의 파일 기록을 확인합니다.
- `source`, 외부 저장소와 `revision`, `upstream_sha256`: 고정된 외부 upstream 자료와 그 증거. 로컬 `source/` 폴더를 뜻하지 않습니다.
- `derivation`: 과거 중간 파생 경로와 revision의 증거. 현재 경로로 바꿔 적는 필드가 아닙니다.
- `sha256`: 별도 검토한 현재 작성 원본의 해시. 준비 도구가 변경을 자동 승인하지 않습니다.

설치 패키지의 `provenance.json`에서는 `local`이 **플러그인 기준 경로**, `canonical_source`가 **저장소 기준 원본 경로**입니다.
원본을 바꿀 때는 [출처·변환 규칙](provenance.md)과 [유지보수 계약](../AGENTS.md)을 함께 확인합니다.

## 준비와 설치는 다른 단계입니다

`scripts/build_plugins.py`는 스킬을 컴파일하거나 `source/`에서 복사하는 도구가 아닙니다.
작성 원본과 검토한 해시를 검증하고, manifest·인덱스·출처/해시·역할 어댑터·필요한 자료 사본만 준비합니다.
원본 스킬 트리와 전체 `plugins/`를 덮어쓰거나 삭제하지 않습니다. `--check`는 쓰지 않고 예상 결과와 비교합니다.

Git에는 이렇게 준비된 설치 파일이 포함됩니다. **`codex plugin add`는 선택한 준비된 패키지를 설치하며,
이 저장소의 Python 준비 스크립트를 자동 실행하지 않습니다.** 호스트 캐시나 사용자 설정을 수정해서 원본을 고치는 방식은 사용하지 않습니다.
설치·활성화·신뢰·새 세션의 발견·실제 호출·지침 준수는 서로 다른 확인 항목입니다.
유지보수 명령은 [README](../README.md#maintain-and-verify), 호스트별 절차는 [호스트 안내](hosts.md)를 따릅니다.

## 스캐폴딩과 업데이트 경계

[`project-blueprints`](https://github.com/KongPedia/project-blueprints)는 Copier 질문·프로필·스타터·프로젝트 설정을 소유합니다.
이 저장소는 재사용 스킬·플러그인·공유 자료·역할 원본을 소유합니다. 프로필은 안정된 플러그인 ID를 선택하며,
여러 프로필의 공통 번들은 합집합으로 중복 제거합니다. 스킬 본문을 프로젝트에 다시 복사하지 않습니다.
프로필이나 Copier 생성/업데이트 방법은 해당 저장소 문서를 사용하고, 여기서 별도 절차를 유지하지 않습니다.

소비 프로젝트는 실제 코드·명령·계약·디자인 결정·안전 권한을, 호스트는 설치 캐시·인증·신뢰·갱신을 소유합니다.
플러그인 갱신과 Copier 프로젝트 구조 업데이트는 별도 채널입니다.
또한 로컬 `catalog.json`의 버전은 작성 중인 패키지 버전이지 원격 태그/릴리스 게시의 증거가 아닙니다.
이전 태그를 사용한 설치 예시와 현재 체크아웃의 내용은 [릴리스·롤백 안내](releases.md)에 따라 구분합니다.
