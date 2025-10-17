`docker build --no-cache --platform=linux/amd64 -t fresco-microservice .`

`docker run -d \
  -e SUPABASE_URL=URL \
  -e SUPABASE_KEY=KEY \
  -p 8000:8000 \
  fresco-microservice`