"""
Prediction module — wraps the trained XGBoost model as a singleton.

Usage:
    from backend.ml.predict import predictor
    result = predictor.predict(flow_features_dict)
"""

import os
import logging

import pandas as pd
import joblib

from backend.config import MODEL_PATH, FEATURE_COLUMNS_PATH

logger = logging.getLogger(__name__)


class IDSPredictor:
    """Loads the trained IDS model and provides a ``predict`` method."""

    def __init__(self):
        self.model = None
        self.feature_columns = None
        self._loaded = False
        self._load_model()

    def _load_model(self):
        try:
            if not os.path.exists(MODEL_PATH):
                logger.warning(
                    "Model file not found at '%s'. "
                    "Run 'python -m backend.ml.train' first.",
                    MODEL_PATH,
                )
                return
            if not os.path.exists(FEATURE_COLUMNS_PATH):
                logger.warning(
                    "Feature columns file not found at '%s'. "
                    "Run 'python -m backend.ml.train' first.",
                    FEATURE_COLUMNS_PATH,
                )
                return

            self.model = joblib.load(MODEL_PATH)
            self.feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
            self._loaded = True
            logger.info("IDS model loaded successfully (%d features).", len(self.feature_columns))
        except Exception as exc:
            logger.error("Failed to load IDS model: %s", exc)
            self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, flow_features: dict) -> dict:
        """
        Predict whether a flow is NORMAL or MALICIOUS.

        Parameters
        ----------
        flow_features : dict
            Feature dict produced by ``FlowData.compute_features()``.

        Returns
        -------
        dict with keys ``label``, ``confidence``, ``raw_prediction``.
        """
        if not self._loaded:
            # Fallback — treat everything as normal when no model is loaded
            return {
                "label": "NORMAL",
                "confidence": 0.0,
                "raw_prediction": 0,
                "attack_type": None,
            }

        # Extract features in the correct order as a NumPy array
        features_list = []
        for col in self.feature_columns:
            features_list.append(float(flow_features.get(col, 0.0)))
        
        import numpy as np
        X = np.array([features_list], dtype=np.float32)

        # Replace any NaN/Inf with 0
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        # Use the model directly on the NumPy array
        raw_pred = int(self.model.predict(X)[0])
        proba = self.model.predict_proba(X)[0]

        # Confidence = probability of the predicted class
        confidence = round(float(proba[raw_pred]), 4)

        label = "MALICIOUS" if raw_pred == 1 else "NORMAL"

        # Infer attack type based on flow characteristics
        attack_type = self._infer_attack_type(flow_features) if raw_pred == 1 else None

        return {
            "label": label,
            "confidence": confidence,
            "raw_prediction": raw_pred,
            "attack_type": attack_type,
        }

    def _infer_attack_type(self, flow_features: dict) -> str:
        """Infer attack type from flow features using multiple detection methods."""
        # Get key features
        dst_port = flow_features.get("Destination Port", 0)
        src_port = flow_features.get("Source Port", 0)
        total_packets = flow_features.get("Total Fwd Packets", 0) + flow_features.get("Total Backward Packets", 0)
        fwd_packets = flow_features.get("Total Fwd Packets", 0)
        bwd_packets = flow_features.get("Total Backward Packets", 0)
        
        # TCP flag counts
        syn_count = flow_features.get("SYN Flag Count", 0)
        rst_count = flow_features.get("RST Flag Count", 0)
        fin_count = flow_features.get("FIN Flag Count", 0)
        ack_count = flow_features.get("ACK Flag Count", 0)
        
        # Flow statistics
        flow_bytes = flow_features.get("Total Length of Fwd Packets", 0) + flow_features.get("Total Length of Bwd Packets", 0)
        flow_packets_per_sec = flow_features.get("Flow Packets/s", 0)
        flow_bytes_per_sec = flow_features.get("Flow Bytes/s", 0)
        
        # Packet length stats
        fwd_mean = flow_features.get("Fwd Packet Length Mean", 0)
        bwd_mean = flow_features.get("Bwd Packet Length Mean", 0)
        
        # Port-based attack classification
        port_attacks = {
            80: "Web Attack", 443: "Web Attack", 8080: "Web Attack", 8443: "Web Attack",
            22: "Brute Force SSH", 23: "Telnet Attack", 21: "FTP Attack",
            25: "Email Attack", 587: "Email Attack", 110: "Email Attack",
            53: "DNS Attack", 123: "NTP Attack",
            3389: "RDP Attack", 445: "SMB Attack", 139: "NetBIOS Attack",
            1433: "SQL Injection", 3306: "MySQL Attack", 5432: "PostgreSQL Attack",
            6379: "Redis Attack", 27017: "MongoDB Attack",
            500: "VPN Attack", 4500: "VPN Attack",
            67: "DHCP Attack", 68: "DHCP Attack",
        }
        
        # Check for specific ports first
        if dst_port in port_attacks:
            return port_attacks[dst_port]
        
        # SYN Flood detection - high SYN ratio, low data transfer
        if total_packets > 0:
            syn_ratio = syn_count / total_packets
            if syn_ratio > 0.7 and flow_bytes_per_sec < 1000 and total_packets > 10:
                return "SYN Flood"
        
        # RST Flood detection
        if rst_count > 5 or (total_packets > 0 and rst_count / total_packets > 0.1):
            return "RST Flood"
        
        # ACK Flood detection
        if total_packets > 0:
            ack_ratio = ack_count / total_packets
            if ack_ratio > 0.8 and flow_packets_per_sec > 50:
                return "ACK Flood"
        
        # Port Scan detection - many different ports, minimal data exchange
        if src_port > 49152 and dst_port not in [80, 443, 22, 21, 25, 53]:
            if flow_bytes_per_sec < 500 and total_packets < 5:
                return "Port Scan"
        
        # Small packet attack - lots of small packets
        if total_packets > 20 and flow_bytes / total_packets < 50 and flow_packets_per_sec > 50:
            return "Small Packet Flood"
        
        # Data exfiltration detection - high bytes out ratio
        if total_packets > 0:
            fwd_ratio = fwd_packets / total_packets
            if fwd_ratio > 0.9 and flow_bytes > 100000:
                return "Data Exfiltration"
        
        # Web scan detection - many HTTP-like requests to same dest
        if bwd_packets == 0 and fwd_packets > 5 and dst_port in [80, 443, 8080]:
            return "Web Scanning"
        
        # Slowloris - low bandwidth, long duration, many small packets
        flow_duration = flow_features.get("Flow Duration", 0)
        if flow_duration > 1000000 and flow_bytes_per_sec < 100 and total_packets > 20:
            return "Slowloris Attack"
        
        return "Unknown Attack"

    def predict_batch(self, df: pd.DataFrame) -> dict:
        if not self._loaded:
            return {"total": len(df), "malicious": 0, "normal": len(df), "attack_types": {}}
        
        # Align columns to training order
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        # Create a copy with only needed features
        df_aligned = df[self.feature_columns].copy()
        
        df_aligned.fillna(0, inplace=True)
        df_aligned.replace([float("inf"), float("-inf")], 0, inplace=True)

        # Predict
        preds = self.model.predict(df_aligned)
        
        malicious_count = int(sum(preds == 1))
        total = len(df)
        
        # Get attack types for malicious predictions
        attack_types = {}
        if malicious_count > 0:
            # Important: iterate using index-agnostic method to avoid mismatch if df had non-standard index
            for i in range(len(preds)):
                if preds[i] == 1:
                    features = df_aligned.iloc[i].to_dict()
                    attack_type = self._infer_attack_type(features)
                    attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
        
        return {
            "total": total,
            "malicious": malicious_count,
            "normal": total - malicious_count,
            "attack_types": attack_types
        }

# Singleton instance — importable from anywhere
predictor = IDSPredictor()
