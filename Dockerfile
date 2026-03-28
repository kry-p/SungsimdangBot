FROM python:3.12-slim

WORKDIR /app

# 의존성 레이어 (pyproject.toml 변경 시에만 재빌드)
COPY pyproject.toml .
RUN mkdir -p config modules resources bin && \
    touch config/__init__.py modules/__init__.py resources/__init__.py bin/__init__.py && \
    pip install --no-cache-dir . && \
    rm -rf config modules resources bin

# 소스 + 패키지 설치 레이어
COPY . .
RUN pip install --no-cache-dir --no-deps . && \
    useradd -m -u 1000 bot && \
    mkdir -p /app/data /app/log && chown -R bot:bot /app/data /app/log
ENV PYTHONPATH=/app
# NOTE: non-root 전환. 기존 root로 생성된 data/ 볼륨은 호스트에서
# chown -R 1000:1000 ./data 실행 필요 (CD 워크플로우에서 자동 처리)
USER bot

CMD ["python", "bin/main.py"]
