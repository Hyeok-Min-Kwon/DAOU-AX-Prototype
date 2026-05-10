FROM node:20-alpine

WORKDIR /app

# 의존성 명세만 먼저 복사 → 레이어 캐시 활용
COPY package.json ./
RUN npm install

# 애플리케이션 코드는 docker-compose에서 볼륨 마운트로 주입 (HMR 지원)
EXPOSE 5173

CMD ["npm", "run", "dev"]
