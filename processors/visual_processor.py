"""
VISUAL PROCESSOR - Camera Image Analysis
Handles ESP32-CAM image data for smoke/fire detection

Weight: 30% (Contextual confirmation, not primary detection)
"""

from typing import Dict, Optional, Tuple
import numpy as np


class VisualProcessor:
    """
    Processes camera image data into visual fire indicators.
    
    Secondary detection modality:
    - Provides contextual confirmation of chemical signals
    - Fragile: lighting dependent, occlusion prone
    - Adds semantic validation ("Is this smoke or just chemicals?")
    
    Detects:
    1. Smoke Presence - Edge density reduction + gray haze
    2. Color Shift - Gray/brown haze vs clear air
    3. Brightness Anomaly - Fire glow or unusual lighting
    4. Spatial Diffusion - Smoke spread patterns
    
    Note: For embedded systems (ESP32-CAM), we use lightweight algorithms
    that don't require deep learning models.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize visual processor with detection parameters
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or self._default_config()
        
        # Historical baseline (for change detection)
        self.brightness_baseline = None
        self.color_baseline = None
        self.edge_density_baseline = None
        
        # Baseline sample collection
        self.baseline_samples = []
        self.max_baseline_samples = 30
    
    def _default_config(self) -> Dict:
        """
        Default detection parameters
        
        Returns:
            Default config dict
        """
        return {
            # Smoke detection thresholds
            'edge_density_threshold': 0.3,    # 30% edge reduction = smoke
            'gray_haze_threshold': 0.4,       # 40% grayness = smoke
            'smoke_confidence_threshold': 0.6, # Minimum confidence for smoke
            
            # Brightness anomaly thresholds
            'brightness_spike_threshold': 1.5,  # 1.5x brighter = fire glow
            'brightness_drop_threshold': 0.5,   # 0.5x darker = smoke obscuration
            
            # Color shift thresholds
            'color_saturation_drop': 0.3,      # 30% less color = gray smoke
            
            # Spatial diffusion
            'diffusion_edge_threshold': 0.4,   # How blurred edges must be
            
            # Image processing
            'resize_width': 160,               # Downsample for speed
            'resize_height': 120,
        }
    
    def process(self, validated_readings: Dict) -> Dict[str, float]:
        """
        Analyze camera image for smoke/fire indicators
        
        Args:
            validated_readings: Dict of Phase-1 validated sensor readings
                Expected key: 'CAMERA' with image data
                Image format: numpy array (H, W, 3) RGB or grayscale
        
        Returns:
            Visual state dict with normalized scores (0.0-1.0):
            {
                'smoke_presence': float,
                'color_shift': float,
                'brightness_anomaly': float,
                'spatial_diffusion': float,
                'visual_confidence': float
            }
        """
        visual_state = {}
        
        # Check if camera data is available
        if 'CAMERA' not in validated_readings:
            # No camera data - return zeros
            return {
                'smoke_presence': 0.0,
                'color_shift': 0.0,
                'brightness_anomaly': 0.0,
                'spatial_diffusion': 0.0,
                'visual_confidence': 0.0
            }
        
        camera_result = validated_readings['CAMERA']
        image = camera_result.value  # Numpy array
        
        # Validate image format
        if not self._is_valid_image(image):
            return {
                'smoke_presence': 0.0,
                'color_shift': 0.0,
                'brightness_anomaly': 0.0,
                'spatial_diffusion': 0.0,
                'visual_confidence': 0.0
            }
        
        # Preprocess image
        processed_image = self._preprocess_image(image)
        
        # =====================================================================
        # 1. SMOKE PRESENCE - Edge density + gray haze
        # =====================================================================
        smoke_score = self._detect_smoke(processed_image)
        visual_state['smoke_presence'] = smoke_score
        
        # =====================================================================
        # 2. COLOR SHIFT - Gray haze detection
        # =====================================================================
        color_shift_score = self._detect_color_shift(processed_image)
        visual_state['color_shift'] = color_shift_score
        
        # =====================================================================
        # 3. BRIGHTNESS ANOMALY - Fire glow or smoke obscuration
        # =====================================================================
        brightness_score = self._detect_brightness_anomaly(processed_image)
        visual_state['brightness_anomaly'] = brightness_score
        
        # =====================================================================
        # 4. SPATIAL DIFFUSION - Smoke spread pattern
        # =====================================================================
        diffusion_score = self._analyze_diffusion_pattern(processed_image)
        visual_state['spatial_diffusion'] = diffusion_score
        
        # =====================================================================
        # 5. VISUAL CONFIDENCE - How reliable is this visual reading?
        # =====================================================================
        # Use Phase-1 reliability + lighting conditions
        base_confidence = camera_result.reliability_score
        lighting_penalty = self._compute_lighting_penalty(processed_image)
        
        visual_state['visual_confidence'] = base_confidence * (1.0 - lighting_penalty)
        
        return visual_state
    
    # =========================================================================
    # IMAGE PREPROCESSING
    # =========================================================================
    
    def _is_valid_image(self, image) -> bool:
        """
        Check if image is valid numpy array
        
        Args:
            image: Input image (should be numpy array)
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(image, np.ndarray):
            return False
        
        if len(image.shape) < 2:
            return False
        
        return True
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for analysis
        
        - Resize to standard size (for speed)
        - Convert to grayscale if needed
        - Normalize to 0-1 range
        
        Args:
            image: Raw image from camera
        
        Returns:
            Preprocessed image
        """
        # If color image, keep it for color shift detection
        # But also compute grayscale version for edge detection
        
        # Normalize to 0-1 if needed
        if image.max() > 1.0:
            image = image.astype(np.float32) / 255.0
        
        return image
    
    # =========================================================================
    # SMOKE DETECTION
    # =========================================================================
    
    def _detect_smoke(self, image: np.ndarray) -> float:
        """
        Detect smoke using edge density reduction + gray haze
        
        Smoke has two key visual properties:
        1. Blurs edges (reduces edge density)
        2. Creates gray haze (desaturates colors)
        
        Args:
            image: Preprocessed image
        
        Returns:
            Smoke score: 0.0 (no smoke) to 1.0 (heavy smoke)
        """
        # Convert to grayscale if color
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image
        
        # Compute edge density
        edge_density = self._compute_edge_density(gray)
        
        # Initialize baseline if needed
        if self.edge_density_baseline is None:
            self.edge_density_baseline = edge_density
            return 0.0
        
        # Compute reduction from baseline
        edge_reduction = (self.edge_density_baseline - edge_density) / self.edge_density_baseline
        edge_reduction = max(0.0, edge_reduction)  # Clamp to positive
        
        # Compute gray haze
        gray_haze_score = self._compute_gray_haze(image)
        
        # Combine edge reduction + gray haze
        smoke_score = (edge_reduction * 0.6 + gray_haze_score * 0.4)
        
        # Threshold-based normalization
        threshold = self.config['smoke_confidence_threshold']
        if smoke_score < threshold:
            return 0.0
        else:
            # Normalize above threshold to 0-1
            normalized = (smoke_score - threshold) / (1.0 - threshold)
            return min(normalized, 1.0)
    
    def _compute_edge_density(self, gray_image: np.ndarray) -> float:
        """
        Compute edge density using simple gradient
        
        Args:
            gray_image: Grayscale image
        
        Returns:
            Edge density (0.0-1.0)
        """
        # Compute gradients (simple Sobel-like)
        dy = np.gradient(gray_image, axis=0)
        dx = np.gradient(gray_image, axis=1)
        
        # Edge magnitude
        edge_magnitude = np.sqrt(dx**2 + dy**2)
        
        # Edge density = fraction of pixels with strong edges
        edge_threshold = 0.1
        edge_pixels = np.sum(edge_magnitude > edge_threshold)
        total_pixels = edge_magnitude.size
        
        edge_density = edge_pixels / total_pixels
        return edge_density
    
    def _compute_gray_haze(self, image: np.ndarray) -> float:
        """
        Detect gray haze (smoke desaturates colors)
        
        Args:
            image: Image (can be color or grayscale)
        
        Returns:
            Gray haze score: 0.0 (clear) to 1.0 (heavy haze)
        """
        if len(image.shape) < 3:
            # Grayscale image - can't compute color saturation
            return 0.0
        
        # Compute color saturation
        # Saturation = max(R,G,B) - min(R,G,B)
        max_channel = np.max(image, axis=2)
        min_channel = np.min(image, axis=2)
        saturation = max_channel - min_channel
        
        # Average saturation
        avg_saturation = np.mean(saturation)
        
        # Initialize baseline if needed
        if self.color_baseline is None:
            self.color_baseline = avg_saturation
            return 0.0
        
        # Compute saturation drop from baseline
        saturation_drop = (self.color_baseline - avg_saturation) / self.color_baseline
        saturation_drop = max(0.0, saturation_drop)  # Clamp to positive
        
        # Normalize to 0-1
        threshold = self.config['color_saturation_drop']
        if saturation_drop < threshold:
            return 0.0
        else:
            normalized = (saturation_drop - threshold) / (1.0 - threshold)
            return min(normalized, 1.0)
    
    # =========================================================================
    # COLOR SHIFT DETECTION
    # =========================================================================
    
    def _detect_color_shift(self, image: np.ndarray) -> float:
        """
        Detect shift toward gray/brown (smoke colors)
        
        Args:
            image: Preprocessed image
        
        Returns:
            Color shift score: 0.0 (no shift) to 1.0 (heavy shift)
        """
        if len(image.shape) < 3:
            # Grayscale - can't detect color shift
            return 0.0
        
        # Compute average color
        avg_r = np.mean(image[:, :, 0])
        avg_g = np.mean(image[:, :, 1])
        avg_b = np.mean(image[:, :, 2])
        
        # Smoke tends to be gray/brown: R ≈ G ≈ B (or R slightly > G,B)
        # Compute how "gray" the image is
        color_variance = np.var([avg_r, avg_g, avg_b])
        
        # Low variance = gray (smoke)
        # High variance = colorful (clear day)
        grayness = 1.0 - min(color_variance * 10, 1.0)  # Scale variance
        
        return grayness
    
    # =========================================================================
    # BRIGHTNESS ANOMALY DETECTION
    # =========================================================================
    
    def _detect_brightness_anomaly(self, image: np.ndarray) -> float:
        """
        Detect brightness anomalies
        
        Two types:
        1. Brightness spike (fire glow)
        2. Brightness drop (smoke obscuration)
        
        Args:
            image: Preprocessed image
        
        Returns:
            Brightness anomaly score: 0.0 (normal) to 1.0 (anomaly)
        """
        # Compute average brightness
        if len(image.shape) == 3:
            brightness = np.mean(image)
        else:
            brightness = np.mean(image)
        
        # Initialize baseline if needed
        if self.brightness_baseline is None:
            self.brightness_baseline = brightness
            return 0.0
        
        # Compute ratio to baseline
        brightness_ratio = brightness / self.brightness_baseline
        
        # Check for spike (fire glow)
        spike_threshold = self.config['brightness_spike_threshold']
        if brightness_ratio > spike_threshold:
            spike_score = min((brightness_ratio - spike_threshold) / spike_threshold, 1.0)
            return spike_score
        
        # Check for drop (smoke obscuration)
        drop_threshold = self.config['brightness_drop_threshold']
        if brightness_ratio < drop_threshold:
            drop_score = min((drop_threshold - brightness_ratio) / drop_threshold, 1.0)
            return drop_score
        
        return 0.0
    
    # =========================================================================
    # SPATIAL DIFFUSION ANALYSIS
    # =========================================================================
    
    def _analyze_diffusion_pattern(self, image: np.ndarray) -> float:
        """
        Analyze spatial diffusion pattern (smoke spread)
        
        Smoke has characteristic diffusion patterns:
        - Blurred edges
        - Non-uniform distribution
        - Gradient from source
        
        Args:
            image: Preprocessed image
        
        Returns:
            Diffusion score: 0.0 (no diffusion) to 1.0 (clear diffusion)
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image
        
        # Compute local standard deviation (texture measure)
        # Smoke creates low-texture regions (blurred)
        
        # Simple approach: compute variance in local patches
        h, w = gray.shape
        patch_size = 16
        
        low_texture_count = 0
        total_patches = 0
        
        for i in range(0, h - patch_size, patch_size):
            for j in range(0, w - patch_size, patch_size):
                patch = gray[i:i+patch_size, j:j+patch_size]
                patch_variance = np.var(patch)
                
                # Low variance = low texture (smoke)
                if patch_variance < self.config['diffusion_edge_threshold']:
                    low_texture_count += 1
                
                total_patches += 1
        
        if total_patches == 0:
            return 0.0
        
        # Fraction of low-texture patches
        diffusion_score = low_texture_count / total_patches
        return diffusion_score
    
    # =========================================================================
    # LIGHTING PENALTY
    # =========================================================================
    
    def _compute_lighting_penalty(self, image: np.ndarray) -> float:
        """
        Compute penalty for poor lighting conditions
        
        Visual detection is less reliable:
        - At night (too dark)
        - In direct sun (too bright, glare)
        - In fog/rain (obscured)
        
        Args:
            image: Preprocessed image
        
        Returns:
            Penalty: 0.0 (good lighting) to 1.0 (terrible lighting)
        """
        # Compute brightness
        brightness = np.mean(image)
        
        # Too dark penalty
        if brightness < 0.2:
            dark_penalty = (0.2 - brightness) / 0.2
            return min(dark_penalty, 1.0)
        
        # Too bright penalty
        if brightness > 0.8:
            bright_penalty = (brightness - 0.8) / 0.2
            return min(bright_penalty, 1.0)
        
        # Good lighting
        return 0.0
    
    # =========================================================================
    # BASELINE CALIBRATION
    # =========================================================================
    
    def calibrate_baseline(self, clean_images: list):
        """
        Calibrate baseline from clean environment images
        
        Use this during installation to learn normal appearance
        
        Args:
            clean_images: List of images from clean environment (no smoke/fire)
        """
        if not clean_images:
            return
        
        edge_densities = []
        brightnesses = []
        saturations = []
        
        for image in clean_images:
            processed = self._preprocess_image(image)
            
            # Compute edge density
            if len(processed.shape) == 3:
                gray = np.mean(processed, axis=2)
            else:
                gray = processed
            edge_density = self._compute_edge_density(gray)
            edge_densities.append(edge_density)
            
            # Compute brightness
            brightness = np.mean(processed)
            brightnesses.append(brightness)
            
            # Compute saturation
            if len(processed.shape) == 3:
                max_channel = np.max(processed, axis=2)
                min_channel = np.min(processed, axis=2)
                saturation = np.mean(max_channel - min_channel)
                saturations.append(saturation)
        
        # Set baselines as medians
        self.edge_density_baseline = np.median(edge_densities)
        self.brightness_baseline = np.median(brightnesses)
        if saturations:
            self.color_baseline = np.median(saturations)
        
        print(f"✅ Visual baselines calibrated:")
        print(f"   Edge density: {self.edge_density_baseline:.3f}")
        print(f"   Brightness: {self.brightness_baseline:.3f}")
        if saturations:
            print(f"   Saturation: {self.color_baseline:.3f}")
    
    def get_statistics(self) -> Dict:
        """
        Get processor statistics
        
        Returns:
            Dict with processing stats
        """
        return {
            'edge_density_baseline': self.edge_density_baseline,
            'brightness_baseline': self.brightness_baseline,
            'color_baseline': self.color_baseline,
            'config': self.config
        }
