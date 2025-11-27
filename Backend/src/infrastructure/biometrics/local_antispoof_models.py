"""
Utility classes to load locally provided anti-spoofing models (AASIST, RawNet2, Nes2Net).

These helpers avoid direct SpeechBrain downloads by consuming the checkpoints
stored under `Backend/models/Anti-Spoofing`.
"""

from __future__ import annotations

import importlib.util
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import torch
import torch.nn.functional as F
import yaml

logger = logging.getLogger(__name__)


def _load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_audio_length(waveform: torch.Tensor, target_len: int) -> torch.Tensor:
    """Pad/crop waveform to the desired length."""
    if waveform.ndim > 1:
        waveform = waveform.squeeze(0)
    total = waveform.shape[-1]
    if total == target_len:
        return waveform
    if total < target_len:
        pad = target_len - total
        return F.pad(waveform, (0, pad))
    start = 0
    if total - target_len > 0:
        start = (total - target_len) // 2
    return waveform[start : start + target_len]


@dataclass
class LocalModelPaths:
    project_root: Path

    @property
    def anti_spoof_root(self) -> Path:
        return self.project_root / "models" / "Anti-Spoofing"

    @property
    def rawnet_dir(self) -> Path:
        return self.anti_spoof_root / "rawnet2"

    @property
    def aasist_dir(self) -> Path:
        return self.anti_spoof_root / "aasist"

    @property
    def nes2net_dir(self) -> Path:
        return self.anti_spoof_root / "nes2net"


class BaseLocalAntiSpoofModel:
    def __init__(self, device: torch.device):
        self.device = device
        self.available = False

    def predict_spoof_probability(
        self, waveform: torch.Tensor, sample_rate: int
    ) -> Optional[float]:
        raise NotImplementedError


class LocalRawNet2Model(BaseLocalAntiSpoofModel):
    def __init__(self, device: torch.device, paths: LocalModelPaths):
        super().__init__(device)
        self._config_path = paths.rawnet_dir / "model_config_RawNet.yaml"
        self._checkpoint_path = paths.rawnet_dir / "pre_trained_DF_RawNet2.pth"
        self._module_path = paths.rawnet_dir / "rawnet2.py"
        self._model = None
        self._target_len = 64600
        self._load_model()

    def _load_model(self):
        if not self._config_path.exists() or not self._checkpoint_path.exists():
            logger.warning("RawNet2 files not found. Skipping local RawNet2 model.")
            return
        try:
            config = yaml.safe_load(self._config_path.read_text())
            model_args = config.get("model", {})
            self._target_len = int(model_args.get("nb_samp", self._target_len))
            module = _load_module(self._module_path, "local_rawnet2")
            RawNet = getattr(module, "RawNet")
            self._model = RawNet(model_args, device=self.device).to(self.device)
            state = torch.load(self._checkpoint_path, map_location=self.device)
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            self._model.load_state_dict(state, strict=False)
            self._model.eval()
            self.available = True
            logger.info("Local RawNet2 anti-spoofing model loaded")
        except Exception as exc:
            logger.warning("Failed to load RawNet2 model: %s", exc)
            self._model = None
            self.available = False

    def predict_spoof_probability(
        self, waveform: torch.Tensor, sample_rate: int
    ) -> Optional[float]:
        if not self.available or self._model is None:
            return None
        with torch.no_grad():
            vec = _normalize_audio_length(waveform, self._target_len).unsqueeze(0)
            vec = vec.to(self.device)
            logits = self._model(vec)
            probs = torch.softmax(logits, dim=1)
            # Convention: index 1 corresponds to spoof class in RawNet2 release
            return probs[:, 1].item()


class LocalAASISTModel(BaseLocalAntiSpoofModel):
    def __init__(self, device: torch.device, paths: LocalModelPaths):
        super().__init__(device)
        self._config_path = paths.aasist_dir / "AASIST.conf"
        self._checkpoint_path = paths.aasist_dir / "AASIST.pth"
        self._module_path = paths.aasist_dir / "AASIST.py"
        self._model = None
        self._target_len = 64600
        self._load_model()

    def _load_model(self):
        if not self._config_path.exists() or not self._checkpoint_path.exists():
            logger.warning("AASIST files not found. Skipping local AASIST model.")
            return
        try:
            config = json.loads(self._config_path.read_text())
            model_args = config.get("model_config", {})
            self._target_len = int(model_args.get("nb_samp", self._target_len))
            module = _load_module(self._module_path, "local_aasist")
            Model = getattr(module, "Model")
            self._model = Model(model_args).to(self.device)
            state = torch.load(self._checkpoint_path, map_location=self.device)
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            self._model.load_state_dict(state, strict=False)
            self._model.eval()
            self.available = True
            logger.info("Local AASIST anti-spoofing model loaded")
        except Exception as exc:
            logger.warning("Failed to load local AASIST model: %s", exc)
            self._model = None
            self.available = False

    def predict_spoof_probability(
        self, waveform: torch.Tensor, sample_rate: int
    ) -> Optional[float]:
        if not self.available or self._model is None:
            return None
        with torch.no_grad():
            vec = _normalize_audio_length(waveform, self._target_len).unsqueeze(0)
            vec = vec.to(self.device)
            _, logits = self._model(vec)
            probs = torch.softmax(logits, dim=1)
            return probs[:, 1].item()


class LocalNes2NetModel(BaseLocalAntiSpoofModel):
    def __init__(
        self,
        device: torch.device,
        paths: LocalModelPaths,
        agg: str = "SEA",
        dilation: int = 1,
        pool_func: str = "mean",
        se_ratio: Optional[list[int]] = None,
        nes_ratio: Optional[list[int]] = None,
    ):
        super().__init__(device)
        self._module_path = paths.nes2net_dir / "WavLM_Nes2Net_X.py"
        self._checkpoint_path = paths.nes2net_dir / "WavLM_Nes2Net_X_e54_seed42.pt"
        self._agg = agg
        self._dilation = dilation
        self._pool_func = pool_func
        self._se_ratio = se_ratio or [1]
        self._nes_ratio = nes_ratio or [8, 8]
        self._model = None
        self._load_model()

    def _load_model(self):
        if not self._module_path.exists() or not self._checkpoint_path.exists():
            logger.warning("Nes2Net files not found. Skipping local Nes2Net model.")
            return
        try:
            import s3prl  # noqa: F401
        except ImportError:
            logger.warning(
                "s3prl is not installed. Nes2Net model requires s3prl (pip install s3prl)."
            )
            return
        try:
            module = _load_module(self._module_path, "local_nes2net")
            ModelClass = getattr(module, "WavLM_Nes2Net_noRes_w_allT")
            args = SimpleNamespace(
                agg=self._agg,
                dilation=self._dilation,
                pool_func=self._pool_func,
                SE_ratio=self._se_ratio,
                Nes_ratio=self._nes_ratio,
            )
            self._model = ModelClass(args=args, device=self.device).to(self.device)
            state = torch.load(self._checkpoint_path, map_location=self.device)
            if isinstance(state, dict):
                state = (
                    state.get("model_state_dict")
                    or state.get("state_dict")
                    or state.get("model")
                    or state
                )
            self._model.load_state_dict(state, strict=False)
            self._model.eval()
            self.available = True
            logger.info("Local Nes2Net anti-spoofing model loaded")
        except Exception as exc:
            logger.warning("Failed to load local Nes2Net model: %s", exc)
            self._model = None
            self.available = False

    def predict_spoof_probability(
        self, waveform: torch.Tensor, sample_rate: int
    ) -> Optional[float]:
        if not self.available or self._model is None:
            return None
        with torch.no_grad():
            vec = waveform.unsqueeze(0) if waveform.ndim == 1 else waveform
            vec = vec.to(self.device)
            scores = self._model(vec, SSL_freeze=True)
            prob = torch.sigmoid(scores.squeeze()).item()
            return float(prob)


def build_local_model_paths() -> LocalModelPaths:
    project_root = Path(__file__).resolve().parents[3]
    return LocalModelPaths(project_root=project_root)

