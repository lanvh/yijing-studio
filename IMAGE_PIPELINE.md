# Image Generation Pipeline

## Pipeline

User Input

↓

Model Loader

↓

Product Analyzer

↓

Prompt Builder

↓

Image Provider

↓

Result Collector

↓

Quality Checker

↓

Content Writer

↓

User Review

↓

Export

## Product Analyzer

输入商品图。

输出：

category

color

material_guess

logo_description

pattern

shape

critical_features

示例：

{
  "category": "shoes",
  "color": ["white", "green"],
  "critical_features": [
    "green heel panel",
    "white midsole",
    "low-top shape"
  ]
}

## Prompt Builder

提示词必须强调：

保持人物身份

保持商品颜色

保持商品结构

不要修改 Logo

自然手脚

真实摄影

合理光影

## Negative Prompt

根据 Provider 能力决定是否支持。

概念包括：

extra fingers
deformed hands
duplicated shoes
incorrect logo
changed product color
distorted clothing
unreal anatomy

## Output Strategy

不要默认一次只生成一张。

MVP：

允许：

1
2
4
6

长期：

系统应鼓励：

生成候选

↓

质检

↓

挑选

而不是期望每张一次成功。