# 1단계: 빌드
FROM node:16.14.2-alpine as build

WORKDIR /app
COPY . .

# 환경변수 전달
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm install
RUN npm run build

# 2단계: 정적 파일 서빙
FROM node:16.14.2-alpine
WORKDIR /app

RUN npm install -g serve
COPY --from=build /app/build ./build

EXPOSE 3000
CMD ["serve", "-s", "build"]
