# REST API

Base URL:

/api/v1

## Auth

POST /auth/login

GET /auth/me

POST /auth/logout

## AI Models

GET /models

POST /models

GET /models/{id}

PATCH /models/{id}

DELETE /models/{id}

POST /models/{id}/images

POST /models/{id}/generate-reference

## Products

GET /products

POST /products

GET /products/{id}

PATCH /products/{id}

DELETE /products/{id}

POST /products/{id}/images

POST /products/{id}/analyze

## Generation

POST /generation/tasks

GET /generation/tasks

GET /generation/tasks/{id}

POST /generation/tasks/{id}/retry

DELETE /generation/tasks/{id}

## Results

GET /generation/tasks/{id}/results

PATCH /generation/results/{id}

DELETE /generation/results/{id}

## Copy

POST /generation/tasks/{id}/copy

GET /generation/tasks/{id}/copy

## Export

POST /generation/tasks/{id}/export

GET /generation/tasks/{id}/export

## System

GET /health

GET /providers