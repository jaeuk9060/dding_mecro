# 설치 가이드

## 방법 1: 개발 모드로 설치 (권장)

프로젝트 디렉토리에서 다음 명령어를 실행하세요:

```bash
pip install -e .
```

이 방법은 코드를 수정하면 즉시 반영되므로 개발 시 유용합니다.

## 방법 2: 일반 설치

```bash
pip install .
```

## 방법 3: 배포용 패키지 생성

배포용 wheel 파일을 생성하려면:

```bash
# 먼저 build 도구 설치
pip install build

# 패키지 빌드
python -m build
```

이 명령어를 실행하면 `dist/` 폴더에 `.whl` 파일이 생성됩니다.

## 설치 후 사용

설치가 완료되면 다음 명령어로 애플리케이션을 실행할 수 있습니다:

```bash
autoclicker
```

## 제거

설치된 패키지를 제거하려면:

```bash
pip uninstall autoclicker
```

