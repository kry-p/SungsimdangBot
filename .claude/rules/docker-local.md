# 로컬 Docker 실행

## 빌드 및 실행

docker-compose.yml은 GHCR 프로덕션 이미지를 사용하므로, 로컬 테스트 시에는 직접 빌드한다.

```bash
# 빌드
docker build -t sungsimdangbot:local .

# 실행
docker run -d --name sungsimdangbot --env-file .env -v "$(pwd)/data:/app/data" sungsimdangbot:local

# 로그 확인
docker logs sungsimdangbot --tail 10
```

## 종료 및 정리

```bash
docker rm -f sungsimdangbot
```

## 주의사항

- 기존 컨테이너가 있으면 `docker rm -f sungsimdangbot`으로 정리 후 실행
- `.env` 파일이 프로젝트 루트에 있어야 함
- `data/` 디렉토리는 SQLite DB 영속화를 위해 볼륨 마운트
