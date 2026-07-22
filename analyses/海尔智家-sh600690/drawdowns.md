---
type: drawdowns
stock: sh600690
updated: '2026-07-22'
items:
- peak: 1994-01
  peakPrice: 0.21
  trough: 1994-07
  troughPrice: 0.07
  depth: -75.9%
  stock_ret: !!python/object/apply:numpy._core.multiarray.scalar
  - &id001 !!python/object/apply:numpy.dtype
    args:
    - f8
    - false
    - true
    state: !!python/tuple
    - 3
    - <
    - null
    - null
    - null
    - -1
    - -1
    - 0
  - !!binary |
    zczMzMysUMA=
  index_ret: null
  alpha: null
  type: 早期无指数对照
  cause: 早期无指数对照
- peak: 2008-03
  peakPrice: 3.41
  trough: 2008-10
  troughPrice: 1.27
  depth: -73.4%
  stock_ret: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    ZmZmZmZmT8A=
  index_ret: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    ZmZmZmYmTsA=
  alpha: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    AAAAAAAABMA=
  type: 系统性(基本同步指数)
  cause: 系统性(基本同步指数)
- peak: 2002-07
  peakPrice: 1.19
  trough: 2005-10
  troughPrice: 0.56
  depth: -66.5%
  stock_ret: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    MzMzMzNzSsA=
  index_ret: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    ZmZmZmYmQsA=
  alpha: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    mpmZmZmZMMA=
  type: 个股/板块(显著跑输指数)
  cause: 个股/板块(显著跑输指数)
- peak: 1994-09
  peakPrice: 0.21
  trough: 1995-01
  troughPrice: 0.11
  depth: -62.1%
  stock_ret: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    zczMzMzMR8A=
  index_ret: null
  alpha: null
  type: 早期无指数对照
  cause: 早期无指数对照
- peak: 1998-08
  peakPrice: 1.13
  trough: 1999-05
  troughPrice: 0.69
  depth: -56.6%
  stock_ret: !!python/object/apply:numpy._core.multiarray.scalar
  - *id001
  - !!binary |
    MzMzMzNzQ8A=
  index_ret: null
  alpha: null
  type: 早期无指数对照
  cause: 早期无指数对照
summary: 回撤 Alpha 分解:区分系统性(同步指数)与个股(跑输指数)回撤
---

# 回撤分析

每个回撤含个股 vs 指数同期表现,Alpha 为超额收益。