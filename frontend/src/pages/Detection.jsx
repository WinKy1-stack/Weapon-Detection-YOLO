import { useState } from 'react';
import { Upload, Loader2, Image as ImageIcon } from 'lucide-react';
import { detectionAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Detection() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [modelType, setModelType] = useState('yolo');
  const [confidence, setConfidence] = useState(0.5);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleDetect = async () => {
    if (!file) {
      toast.error('Please select an image first');
      return;
    }

    setLoading(true);
    try {
      const response = await detectionAPI.detectImage(file, confidence, modelType);
      setResult(response.data);
      toast.success(`Detected ${response.data.detections.length} weapons`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Detection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Weapon Detection</h1>
        <p className="text-gray-400 mt-1">Upload an image to detect weapons</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="card space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Settings</h3>
            
            {/* Model Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Model
              </label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
              >
                <option value="yolo">YOLOv8m (Fast)</option>
                <option value="fasterrcnn">Faster R-CNN (Accurate)</option>
              </select>
            </div>

            {/* Confidence Threshold */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Confidence: {(confidence * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          {/* Upload Button */}
          <div>
            <label className="block">
              <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors">
                <Upload className="w-12 h-12 mx-auto text-gray-400 mb-2" />
                <p className="text-gray-300 font-medium">Click to upload image</p>
                <p className="text-sm text-gray-400 mt-1">PNG, JPG up to 50MB</p>
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>

          {/* Detect Button */}
          {file && (
            <button
              onClick={handleDetect}
              disabled={loading}
              className="w-full btn btn-primary py-3 disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Detecting...
                </span>
              ) : (
                'Detect Weapons'
              )}
            </button>
          )}
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Preview */}
          {preview && (
            <div className="card">
              <h3 className="text-lg font-semibold text-white mb-4">
                {result ? 'Detection Result' : 'Preview'}
              </h3>
              <img
                src={result?.image_url ? `http://localhost:8000${result.image_url}` : preview}
                alt="Preview"
                className="w-full rounded-lg"
              />
            </div>
          )}

          {/* Detection Details */}
          {result && (
            <div className="card">
              <h3 className="text-lg font-semibold text-white mb-4">Detections</h3>
              
              <div className="mb-4 flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                <span className="text-gray-300">Processing Time</span>
                <span className="text-white font-semibold">
                  {(result.processing_time * 1000).toFixed(0)}ms
                </span>
              </div>

              <div className="space-y-3">
                {result.detections.length > 0 ? (
                  result.detections.map((det, idx) => (
                    <div key={idx} className="p-4 bg-slate-700 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-white font-medium capitalize">
                          {det.class_name}
                        </span>
                        <span className="px-3 py-1 bg-danger-500/20 text-danger-400 rounded-full text-sm font-medium">
                          {(det.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="text-sm text-gray-400">
                        Position: ({det.bbox.x1.toFixed(0)}, {det.bbox.y1.toFixed(0)}) → 
                        ({det.bbox.x2.toFixed(0)}, {det.bbox.y2.toFixed(0)})
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-4">No weapons detected</p>
                )}
              </div>
            </div>
          )}

          {!preview && (
            <div className="card h-96 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <ImageIcon className="w-16 h-16 mx-auto mb-4" />
                <p>Upload an image to start detection</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
