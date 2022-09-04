# 安全编排自动化与响应 (SOAR) - 详细部署

## 1. Mongo 部署

```
docker run -d --restart=always --name xxsoar-mongo -e MONGO_INITDB_ROOT_USERNAME=user -e MONGO_INITDB_ROOT_PASSWORD=password -p 27017:27017 -v /var/log/db:/data/db mongo
```
## 2. Redis 部署
```
docker run -d --restart=always --name xxsoar-redis -p 6379:6379 redis redis-server --requirepass "password"
```

## 3. 微服务部署
```
docker pull alpine:3.15 && docker tag alpine:3.15 gcr.io/iguazio/alpine:3.15

docker run -d --restart=always -p 8070:8070 -v /var/run/docker.sock:/var/run/docker.sock --name nuclio-dashboard xxwsy/nuclio

```

## 4. XXSOAR 部署
 - 写配置 (创建文件 settings.py) 写入以下内容，修改1,2,3步提供的服务配置内容
 
```
# MongoDB 配置
MongoDB_URL = 'mongodb://user:password@IP:27017'
DB_NAME = 'local'

# Redis 配置
Redis_URL = 'redis://:password@IP:6379/0'

# serverless 配置
FAAS_HOST = "http://IP:8070"
```

 - 启动服务

```
docker run -d --restart=always -p 8000:8000 -v $PWD/settings.py:/app/settings.py xxwsy/xxsoar:latest supervisord -c /app/supervisord.conf
```
#### 推荐阅读
[# 安全编排自动化与响应 (SOAR)](https://github.com/xxwsy/xxsoar)

[# Nuclio - "Serverless" for Real-Time Events and Data Processing](https://github.com/nuclio/nuclio)


### 访问地址
```
http://IP:8000
```


### 联系我们
<img src="http://chenyue.tech/assets/img/contactme.jpg" width="200" height="200"/>
