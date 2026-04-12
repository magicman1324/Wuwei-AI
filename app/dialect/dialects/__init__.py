"""方言适配器实现，导入时自动注册到 DialectRegistry。"""

from app.dialect.dialects import cantonese, mandarin, sichuan

__all__ = ["cantonese", "mandarin", "sichuan"]
