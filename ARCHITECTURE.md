# Architecture

## System

Vue Frontend

↓

FastAPI REST API

↓

Application Service

├ User Service
├ Model Service
├ Product Service
├ Generation Service
├ Copy Service
└ Export Service

↓

Provider Layer

├ MockImageProvider
└ RealImageProvider

↓

External AI

## Storage

PostgreSQL：

结构化数据

Object Storage：

原图
模特参考图
生成图
ZIP

## Future

Redis

↓

Generation Queue

↓

Workers

↓

Image Providers

## Rule

Controller 不直接访问 Provider。

Controller：

API
↓

Service
↓

Provider

## Future Provider Router

ProviderRouter 根据：

task_type
cost
quality
availability

选择模型。

MVP 不需要智能路由。

但接口必须保留。