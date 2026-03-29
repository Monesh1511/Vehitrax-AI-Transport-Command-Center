import React, { useState } from 'react';
import { X, Upload } from 'lucide-react';

// Normalize plate same way backend does
const normalizePlate = (plate) => {
  if (!plate) return '';
  return plate.toUpperCase().replace(/[^A-Z0-9]/g, '');
};

export function BusUploadForm({ apiUrl, onSuccess, onClose }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({
    plate_number: '',
    bus_name: '',
    driver_name: '',
    mobile_number: '',
    license_number: '',
    years_of_experience: '',
    shift: 'Morning',
    bus_type: 'AC',
    route: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const normalizedPlate = normalizePlate(formData.plate_number);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    if (!normalizedPlate) {
      setError('Please enter a valid plate number (letters and numbers only)');
      return;
    }

    setIsLoading(true);

    try {
      const payload = {
        ...formData,
        years_of_experience: formData.years_of_experience ? parseInt(formData.years_of_experience) : null,
      };

      const response = await fetch(`${apiUrl}/api/buses/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess(`✓ Bus "${result.bus_name}" with plate ${result.plate_number} added successfully!`);
        setFormData({
          plate_number: '',
          bus_name: '',
          driver_name: '',
          mobile_number: '',
          license_number: '',
          years_of_experience: '',
          shift: 'Morning',
          bus_type: 'AC',
          route: '',
        });
        
        if (onSuccess) {
          setTimeout(onSuccess, 1500);
          setTimeout(onClose, 1500);
        }
      } else {
        const errData = await response.json();
        if (response.status === 409) {
          setError(`⚠ Bus with plate "${normalizedPlate}" already exists in database`);
        } else {
          setError(errData.detail || 'Failed to add bus');
        }
      }
    } catch (err) {
      setError(err.message || 'Error adding bus');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-header">
          <h3 className="modal-title">Upload New Bus</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={22} />
          </button>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-field">
              <label>
                Number Plate *
              </label>
              <input
                type="text"
                name="plate_number"
                value={formData.plate_number}
                onChange={handleChange}
                placeholder="e.g., TN19MD5466 or TN 19 MD 5466"
                required
                className="input"
              />
              {formData.plate_number && (
                <div className="form-hint">
                  <strong>Will be stored as:</strong> {normalizedPlate}
                </div>
              )}
            </div>

            <div className="form-field">
              <label>
                Bus Number *
              </label>
              <input
                type="text"
                name="bus_name"
                value={formData.bus_name}
                onChange={handleChange}
                placeholder="e.g., MSRTC-23"
                required
                className="input"
              />
            </div>

            <div className="form-field">
              <label>
                Driver Name *
              </label>
              <input
                type="text"
                name="driver_name"
                value={formData.driver_name}
                onChange={handleChange}
                placeholder="e.g., Selvam Perumal"
                required
                className="input"
              />
            </div>

            <div className="form-field">
              <label>
                Mobile Number
              </label>
              <input
                type="tel"
                name="mobile_number"
                value={formData.mobile_number}
                onChange={handleChange}
                placeholder="e.g., 7346778616"
                className="input"
              />
            </div>

            <div className="form-field">
              <label>
                License Number
              </label>
              <input
                type="text"
                name="license_number"
                value={formData.license_number}
                onChange={handleChange}
                placeholder="e.g., GJ20117605190"
                className="input"
              />
            </div>

            <div className="form-field">
              <label>
                Years of Experience
              </label>
              <input
                type="number"
                name="years_of_experience"
                value={formData.years_of_experience}
                onChange={handleChange}
                placeholder="e.g., 29"
                min="0"
                className="input"
              />
            </div>

            <div className="form-field">
              <label>
                Shift
              </label>
              <select
                name="shift"
                value={formData.shift}
                onChange={handleChange}
                className="select"
              >
                <option value="Morning">Morning</option>
                <option value="Afternoon">Afternoon</option>
                <option value="Night">Night</option>
              </select>
            </div>

            <div className="form-field">
              <label>
                Bus Type
              </label>
              <select
                name="bus_type"
                value={formData.bus_type}
                onChange={handleChange}
                className="select"
              >
                <option value="AC">AC</option>
                <option value="Non-AC">Non-AC</option>
                <option value="Deluxe">Deluxe</option>
                <option value="Express">Express</option>
                <option value="Ordinary">Ordinary</option>
              </select>
            </div>

            <div className="form-field">
              <label>
                Route
              </label>
              <input
                type="text"
                name="route"
                value={formData.route}
                onChange={handleChange}
                placeholder="e.g., AC / Morning"
                className="input"
              />
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ opacity: isLoading ? 0.6 : 1 }}>
              <Upload size={18} />
              {isLoading ? 'Adding...' : 'Add Bus'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
