# Python 중심 robotics use case

Python 로봇 프로그램은 HTTP API가 없어도 정상적인 애플리케이션입니다. 로봇 연동이라는 이유만으로 FastAPI,
ROS, Dora, Zenoh, 특정 SDK 또는 C++ firmware를 함께 넣지 않습니다. 실제 선택된 기술과 소유 package의 계약이
우선입니다. Sensor/command·freshness·safety/lifecycle 변경에만
[plugin routing](../README.md)에서 `robotics-software`를 선택해 적용합니다.

## 한 가지 조합: 로봇 상태 조회와 명령 요청

여러 프로그램과 실제 공유 코드가 필요한 시점에 monorepo를 선택합니다. 다음은 구현 명령이나 필수 디렉터리가
아닌 책임 배치 예입니다. 각 package 내부의 `src`와 native manifest는 선택한 blueprint가 정합니다.

| Component | 기술/형태 | 책임 | 소유하지 않는 것 |
| --- | --- | --- | --- |
| `robot-agent` | Python 실행 프로그램 | SDK/transport adapter, lifecycle, 로봇 상태 수집과 승인된 실행 경계 | HTTP/UI가 복제한 safety policy |
| `api` | Python FastAPI backend | 인증·입력 검증, 명령 admission/조회, 오류와 상태의 HTTP 매핑 | 로봇의 물리 성공을 추정하는 별도 상태 |
| `web` | React frontend | operator 입력, loading/error/stale 상태, 상관관계가 있는 결과 표시 | 최종 actuation 또는 safety authority |
| `robot-domain` | Python 공유 package | 두 Python consumer가 실제로 공유하는 schema·단위·순수한 불변식 | 네트워크 연결, SDK client, consumer 역방향 import |

`robot-domain`은 실제 공유 consumer가 있을 때만 만듭니다. 작은 single Python 프로그램은 같은 책임을 소수의
모듈/함수로 유지할 수 있습니다. `domain/application/repository` 빈 계층이나 transport abstraction부터 만들지
않습니다. C++ firmware나 Rust 구현이 실제 필요할 때만 해당 component와 계약을 추가합니다.

## 명세 → 경계 → 테스트

요청은 “현재 연결된 로봇에 유효한 명령을 전달하고 결과를 구분해 표시한다”입니다. 구현 전에 다음을 정합니다.

1. **표현:** SDK 좌표/단위와 공유 schema를 구분합니다. Adapter가 변환을 소유하고 알려진 입력/출력 fixture로
   검증합니다. Rotation·frame·axis·timestamp 의미를 field 이름 또는 계약에 명시합니다.
2. **최신성:** capture/receive 시각과 clock domain을 구분합니다. Local monotonic clock으로 deadline을 계산하고,
   재생/시계 jump/재연결 시 오래된 상태를 정상 telemetry로 표시하지 않습니다. 다른 장치의 timestamp를 동기화
   계약 없이 직접 빼지 않습니다.
3. **권한과 결과:** command identity, owner/session, lease와 safety arbitration의 실제 소유자를 확인합니다.
   API의 `queued` ACK는 physical completion이 아닙니다. Timeout은 실패 확정이나 “아무 일도 안 일어남”의 증거가
   아니므로 unknown 결과를 구분하고, 실제 authoritative 상태 확인 없이 재시도하지 않습니다.
4. **수명과 부하:** queue capacity/overload, bounded I/O와 shutdown을 명시합니다. Reconnect는 새 session과
   freshness 확인 후 재개하며 과거 actuation을 자동 재생하지 않습니다. 부분 시작 실패에도 이미 얻은 자원을
   정리하고, waiter cancellation과 thread/remote 작업 종료를 구분합니다.
5. **증거:** fake clock/transport와 replay fixture로 stale/drop/duplicate/reorder, 잘못된 단위·범위, owner expiry,
   cancellation·cleanup 실패를 검증합니다. API는 rejection/status/correlation을, UI는 pending/stale/unknown을
   검증합니다. 순수 policy fake 테스트만으로 실제 SDK adapter까지 검증했다고 쓰지 않습니다.

[Plugin routing](../README.md)으로 common plugin의 기준을 찾아 naming·SRP·configuration·type 경계를 확인하고,
[개발 workflow](development.md)로 명세와 회귀 증거를 연결합니다. 기능이 없는 starter에 실제 로봇 연결이나
운영 성능을 가정하지 않습니다. 이 예시는 설계 설명이며 실행·물리 동작을 검증한 구현이 아닙니다.

## 완료 증거의 한계

Static checks, unit/integration tests, replay, simulation, build와 배포는 각각 별도 증거입니다. 어느 것도 물리
이동·발사·회복·전기적 안전을 대신하지 않습니다. 자동 software gate는 비작동 기본값을 지키며 physical serial,
bus와 hardware-connected broker에 접근하지 않습니다. 실기 작업은 별도 기록된 사람의 승인과 해당 시스템의
안전 절차가 필요합니다.
