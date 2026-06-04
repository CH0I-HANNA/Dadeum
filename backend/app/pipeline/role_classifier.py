from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.core.config import MODELS_DIR

if TYPE_CHECKING:
    from PIL import Image

_IMG_SIZE = 224
_ROLE_NAMES = ["표지", "섹션헤더", "본문", "도표/시각자료", "마무리"]


class RoleClassifier:
    def __init__(self, model, device) -> None:
        self._model = model
        self._device = device

    def predict(self, images: list) -> list[int]:
        """PIL 이미지 리스트 → 역할 인덱스 리스트 (0~4).
        빈 리스트 입력 시 빈 리스트 반환. 배치 크기: 32.
        """
        if not images:
            return []

        import torch
        from torchvision import transforms

        transform = transforms.Compose([
            transforms.Resize((_IMG_SIZE, _IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        results: list[int] = []
        self._model.eval()

        with torch.no_grad():
            for i in range(0, len(images), 32):
                batch = images[i:i + 32]
                tensors = torch.stack(
                    [transform(img.convert("RGB")) for img in batch]
                ).to(self._device)
                logits = self._model(tensors)
                preds = logits.argmax(dim=1).tolist()
                results.extend(preds)

        return results

    @classmethod
    def load(cls) -> Optional["RoleClassifier"]:
        """MODELS_DIR/role_classifier_clip_best.pt 로드.
        파일 미존재, torch/timm 미설치, 로드 실패 시 None 반환 (예외 발생 금지).
        """
        checkpoint_path = MODELS_DIR / "role_classifier_clip_best.pt"

        if not checkpoint_path.exists():
            return None

        try:
            import torch
            import timm
            import torch.nn as nn
        except ImportError:
            return None

        try:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            class SlideRoleClassifier(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.backbone = timm.create_model(
                        "efficientnet_b3", pretrained=False, num_classes=0, global_pool="avg"
                    )
                    self.classifier = nn.Sequential(
                        nn.Dropout(0.3),
                        nn.Linear(1536, 256),
                        nn.ReLU(),
                        nn.Dropout(0.15),
                        nn.Linear(256, 5),
                    )

                def forward(self, x):
                    return self.classifier(self.backbone(x))

            model = SlideRoleClassifier()
            checkpoint = torch.load(checkpoint_path, map_location=device)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.to(device)
            model.eval()

            return cls(model, device)
        except Exception:
            return None
