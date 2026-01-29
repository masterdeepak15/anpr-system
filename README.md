# ANPR System

<div align="center">

![ANPR System](https://img.shields.io/badge/ANPR-System-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge)

**Production-Grade Automatic Number Plate Recognition System**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [API](#-api-reference) • [Demo](#-demo)

</div>

---

## 🎯 Overview

A complete, production-ready ANPR (Automatic Number Plate Recognition) system built from scratch for 24/7 deployment. Designed for **CPU-only processing** with real-time performance, supporting multiple RTSP camera streams simultaneously.

### Key Highlights

- ✅ **CPU-Only Processing** - No GPU required, optimized for Intel/AMD CPUs
- ✅ **Real-Time Performance** - 3-10 FPS per camera with efficient processing
- ✅ **Multi-Camera Support** - Handle 5-15 cameras simultaneously
- ✅ **Built From Scratch** - No pre-packaged ANPR/ALPR libraries
- ✅ **Production-Ready** - Auto-recovery, health monitoring, supervision
- ✅ **REST API + SSE** - Complete API with real-time event streaming
- ✅ **Web Admin Panel** - Beautiful HTML5 admin interface
- ✅ **Indian Formats** - Complete support for all Indian plate formats
- ✅ **Extensible** - Easy to add new countries and customizations

---

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Architecture](#-architecture)
- [Performance](#-performance)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality
- **Multi-Camera RTSP Processing** - Process multiple IP camera streams
- **Vehicle Detection** - ONNX-based vehicle detection (cars, bikes, trucks, buses)
- **Plate Detection** - Hybrid classical CV + ML approach
- **Custom OCR Engine** - Built from scratch with character segmentation
- **Multi-Format Support** - Indian formats: Standard, BH Series, Army, Diplomatic, Temporary, Rental
- **Temporal Aggregation** - Multi-frame voting for accuracy
- **Real-Time Validation** - Format and rule-based validation

### API & Integration
- **REST API** - Full CRUD operations for cameras, results, configuration
- **Server-Sent Events (SSE)** - Real-time plate detection events
- **Image Upload API** - POST image, get detection results
- **Web Admin Panel** - Beautiful HTML5 interface
- **Prometheus Metrics** - Performance monitoring export

### Production Features
- **Auto-Reconnection** - Cameras auto-reconnect on failure
- **Process Supervision** - Auto-restart with failure limits
- **Health Monitoring** - System health checks every 30s
- **Adaptive Performance** - Dynamic frame skipping based on CPU
- **Database Storage** - SQLite for configuration and results
- **Structured Logging** - Comprehensive logging with rotation

---

## 💻 System Requirements

### Minimum Requirements
| Component | Specification |
|-----------|--------------|
| CPU | Intel Core i5 (6th gen) / AMD Ryzen 5 |
| RAM | 4GB |
| Storage | 10GB available space |
| OS | Ubuntu 20.04+ / Debian 11+ |
| Python | 3.11+ |

### Recommended Requirements
| Component | Specification |
|-----------|--------------|
| CPU | Intel Core i7 (8th gen) / AMD Ryzen 7 |
| RAM | 8GB |
| Storage | 20GB SSD |
| OS | Ubuntu 22.04 LTS |
| Python | 3.11 |

### Capacity Estimates
| CPU | Cameras | FPS | CPU Usage | RAM |
|-----|---------|-----|-----------|-----|
| i5-9400 | 2-3 | 3-5 | ~70% | ~1.5GB |
| i7-10700 | 5-8 | 5 | ~80% | ~2.5GB |
| i9-11900K | 10-15 | 5-7 | ~75% | ~4GB |

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/masterdeepak15/anpr-system.git
cd anpr-system
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Download Models
```bash
# Place your ONNX models in models/ directory
# Required files:
# - models/vehicle_detector.onnx
# - models/plate_detector.onnx
# - models/char_classifier.onnx

# Or run download script
./scripts/download_models.sh
```

### 4. Initialize Database
```bash
python scripts/init_db.py
```

### 5. Configure
```bash
# Copy example environment
cp .env.example .env

# Edit config.json with your settings
nano config.json
```

### 6. Run
```bash
# Start the system
python main.py

# With custom config
python main.py --config config.json --log-level INFO

# Access admin panel
open http://localhost:5000/  # or visit in browser
```

---

## 📦 Installation

### Method 1: Standard Installation
```bash
# 1. System dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip python3-dev build-essential

# 2. Clone repository
git clone https://github.com/yourusername/anpr-system.git
cd anpr-system

# 3. Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Initialize
python scripts/init_db.py

# 5. Configure cameras
python scripts/add_cameras.py
```

### Method 2: Docker Installation
```bash
cd deployment/docker
docker-compose up -d

# View logs
docker-compose logs -f anpr-system

# Stop
docker-compose down
```

### Method 3: Systemd Service (Production)
```bash
cd deployment/systemd
sudo ./install.sh

# Start service
sudo systemctl start anpr
sudo systemctl status anpr

# View logs
sudo journalctl -u anpr -f
```

---

## ⚙️ Configuration

### config.json
```json
{
  "frame_width": 640,
  "frame_height": 480,
  "vehicle_model_path": "models/vehicle_detector.onnx",
  "plate_model_path": "models/plate_detector.onnx",
  "ocr_model_path": "models/char_classifier.onnx",
  "country_code": "IN",
  "api_host": "0.0.0.0",
  "api_port": 5000,
  "target_fps": 5.0,
  "max_cpu_percent": 80.0,
  "aggregation_window": 5,
  "min_occurrences": 3,
  "vehicle_confidence": 0.5
}
```

### Environment Variables (.env)
```bash
ANPR_ENV=production
LOG_LEVEL=INFO
API_PORT=5000
API_KEY=your-secure-api-key
DB_PATH=data/anpr_system.db
MAX_WORKERS=4
```

### Adding Cameras

**Via API:**
```bash
curl -X POST http://localhost:5000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "cam_entrance_01",
    "name": "Main Entrance",
    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
    "location": "Building A - Entrance",
    "frame_skip": 2
  }'
```

**Via Web UI:**
1. Open http://localhost:5000
2. Click "Add Camera"
3. Fill in details
4. Submit

---

## 📖 Usage

### Starting the System
```bash
# Basic start
python main.py

# With custom settings
python main.py --config config.json --log-level DEBUG --log-file logs/anpr.log

# Production mode
python main.py --log-level INFO --log-file /var/log/anpr/anpr.log
```

### Using the Admin Panel
1. Open browser: `http://localhost:5000`
2. View real-time statistics
3. Manage cameras
4. Upload images for detection
5. Monitor live detections

### API Usage Examples

**Get System Status:**
```bash
curl http://localhost:5000/api/v1/status
```

**Query Recent Results:**
```bash
curl "http://localhost:5000/api/v1/results?limit=10"
```

**Search for Plate:**
```bash
curl "http://localhost:5000/api/v1/results/search?plate=MH12"
```

**Upload Image for Detection:**
```bash
curl -X POST http://localhost:5000/api/v1/detect/image \
  -F "image=@car_image.jpg"
```

**Real-Time Events (SSE):**
```bash
curl -N http://localhost:5000/api/v1/events/stream
```

---

## 🔌 API Reference

### Endpoints

#### System
- `GET /health` - Health check
- `GET /api/v1/status` - System status and stats

#### Cameras
- `GET /api/v1/cameras` - List all cameras
- `GET /api/v1/cameras/{id}` - Get camera details
- `POST /api/v1/cameras` - Add new camera
- `PUT /api/v1/cameras/{id}` - Update camera
- `DELETE /api/v1/cameras/{id}` - Delete camera

#### Results
- `GET /api/v1/results` - Query results
  - Query params: `camera_id`, `start_time`, `end_time`, `limit`
- `GET /api/v1/results/search?plate={text}` - Search by plate
- `GET /api/v1/results/stats?hours=24` - Get statistics

#### Image Detection
- `POST /api/v1/detect/image` - Upload image for detection
  - Body: `multipart/form-data` with `image` file
  - Returns: Vehicle and plate detections with coordinates

#### Events (SSE)
- `GET /api/v1/events/stream` - Real-time event stream

#### Pipeline Control
- `POST /api/v1/pipeline/start` - Start pipeline
- `POST /api/v1/pipeline/stop` - Stop pipeline
- `POST /api/v1/pipeline/restart` - Restart pipeline

### Response Format

**Detection Result:**
```json
{
  "timestamp": 1706543210.123,
  "image_shape": [1080, 1920, 3],
  "vehicles": [
    {
      "bbox": [100, 200, 400, 500],
      "confidence": 0.95,
      "class_name": "car",
      "plate": {
        "text": "MH12AB1234",
        "confidence": 0.92,
        "bbox": [150, 350, 250, 380],
        "character_confidences": [0.98, 0.96, 0.95, ...],
        "valid": true
      }
    }
  ]
}
```

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        ANPR System Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   RTSP       │────▶│  Frame       │────▶│  Detection   │    │
│  │   Cameras    │     │  Buffers     │     │  Pipeline    │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                                           │            │
│         │                                           ▼            │
│         │                                  ┌──────────────┐     │
│         │                                  │     OCR      │     │
│         │                                  │   Engine     │     │
│         │                                  └──────────────┘     │
│         │                                           │            │
│         │                                           ▼            │
│         │                                  ┌──────────────┐     │
│         └─────────────────────────────────▶│ Validation & │     │
│                                             │ Aggregation  │     │
│                                             └──────────────┘     │
│                                                     │            │
│                                                     ▼            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   SQLite     │◀────│   Results    │◀────│   Storage    │    │
│  │   Database   │     │   Manager    │     │   Layer      │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                                                        │
│         │                                                        │
│  ┌──────▼───────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   REST API   │────▶│   Web UI     │     │   SSE        │    │
│  │   Server     │     │   (HTML5)    │     │   Events     │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

---

## 📊 Performance

### Benchmarks (Intel i7-10700)

| Operation | Time | Throughput |
|-----------|------|------------|
| Vehicle Detection | 80-120ms | 8-12 FPS |
| Plate Detection | 20-30ms | 33-50 FPS |
| OCR Processing | 50-80ms | 12-20 FPS |
| **Full Pipeline** | **150-230ms** | **4-6 FPS** |

### Optimization Tips

1. **Reduce Frame Skip**: Increase `frame_skip` to 3-5 for lower CPU usage
2. **Lower Resolution**: Set `frame_width` to 480 for faster processing
3. **Disable ML Refinement**: Set `use_plate_ml` to `false`
4. **Adjust Workers**: Tune `max_workers` based on CPU cores

---

## 🚢 Deployment

### Production Checklist

- [ ] Hardware meets requirements
- [ ] Network configured, cameras accessible
- [ ] Firewall rules configured
- [ ] SSL certificates obtained
- [ ] Models downloaded and verified
- [ ] Database initialized
- [ ] Cameras added and tested
- [ ] Monitoring enabled (Prometheus/Grafana)
- [ ] Backups automated
- [ ] Team trained

### Monitoring

**Prometheus + Grafana:**
```bash
# Start monitoring stack
cd monitoring
docker-compose up -d

# Access Grafana
open http://localhost:3000
```

**Logs:**
```bash
# View logs
tail -f logs/anpr.log

# Search for errors
grep ERROR logs/anpr.log

# Systemd logs
sudo journalctl -u anpr -f
```

---

## 🐛 Troubleshooting

### Common Issues

**Camera Won't Connect**
```bash
# Test RTSP URL
ffplay rtsp://camera-ip:554/stream1

# Check network
ping camera-ip

# Verify credentials in RTSP URL
```

**High CPU Usage**
- Increase `frame_skip` to 3-5
- Reduce `target_fps`
- Lower `frame_width` and `frame_height`

**Low Detection Rate**
- Check camera angle and lighting
- Verify model files exist
- Review confidence thresholds
- Check plate formats in validation

**Database Locked**
- Check file permissions
- Ensure only one instance running
- Consider PostgreSQL for multi-instance

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed guide.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/anpr-system.git
cd anpr-system

# Create development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ONNX Runtime** - CPU-optimized inference
- **OpenCV** - Image processing
- **Flask** - API framework
- **SQLite** - Database

---

## 📞 Support

- **Documentation**: [Full Docs](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/anpr-system/issues)
- **Email**: support@example.com

---

## 🗺️ Roadmap

- [ ] GPU Support (CUDA)
- [ ] Multi-country support (US, EU, UK)
- [ ] Vehicle make/model recognition
- [ ] Cloud deployment templates
- [ ] Mobile app
- [ ] Advanced analytics dashboard

---

<div align="center">

**Made with ❤️ by ANPR Team**

[⬆ Back to Top](#anpr-system)

</div>