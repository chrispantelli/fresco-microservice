`docker build --no-cache --platform=linux/amd64 -t fresco-microservice .`

`docker run -d \
  -e SUPABASE_URL=URL \
  -e SUPABASE_KEY=KEY \
  -e SUPABASE_STORAGE_GENERATED_REPORTS=GENERATED_REPORTS \
  -p 8000:8000 \
  fresco-microservice`


To run in development
`uvicorn app.main:start_application --factory --host 0.0.0.0 --port 8000`