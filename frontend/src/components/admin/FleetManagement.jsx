import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../../services/admin';

const FleetManagement = () => {
  const [activeTab, setActiveTab] = useState('buses');
  const [showBusModal, setShowBusModal] = useState(false);
  const [selectedBus, setSelectedBus] = useState(null);
  const [busFormData, setBusFormData] = useState({
    license_plate: '',
    model: '',
    capacity: '',
    amenities: []
  });

  const queryClient = useQueryClient();

  const { data: busesData, isLoading: busesLoading } = useQuery({
    queryKey: ['admin-buses'],
    queryFn: () => adminService.getBuses(),
    enabled: activeTab === 'buses',
  });

  const { data: driversData, isLoading: driversLoading } = useQuery({
    queryKey: ['admin-drivers'],
    queryFn: () => adminService.getDrivers(),
    enabled: activeTab === 'drivers',
  });

  const createBusMutation = useMutation({
    mutationFn: (busData) => adminService.createBus(busData),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-buses']);
      setShowBusModal(false);
      setBusFormData({ license_plate: '', model: '', capacity: '', amenities: [] });
    },
  });

  const updateBusMutation = useMutation({
    mutationFn: ({ busId, busData }) => adminService.updateBus(busId, busData),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-buses']);
      setShowBusModal(false);
      setSelectedBus(null);
    },
  });

  const handleBusSubmit = (e) => {
    e.preventDefault();
    const formData = {
      ...busFormData,
      capacity: parseInt(busFormData.capacity),
      amenities: busFormData.amenities
    };

    if (selectedBus) {
      updateBusMutation.mutate({ busId: selectedBus.id, busData: formData });
    } else {
      createBusMutation.mutate(formData);
    }
  };

  const handleEditBus = (bus) => {
    setSelectedBus(bus);
    setBusFormData({
      license_plate: bus.license_plate,
      model: bus.model,
      capacity: bus.capacity.toString(),
      amenities: bus.amenities || []
    });
    setShowBusModal(true);
  };

  const handleAmenityChange = (amenity) => {
    setBusFormData(prev => ({
      ...prev,
      amenities: prev.amenities.includes(amenity)
        ? prev.amenities.filter(a => a !== amenity)
        : [...prev.amenities, amenity]
    }));
  };

  const BusModal = () => (
    <div className="modal-overlay" onClick={() => setShowBusModal(false)}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{selectedBus ? 'Edit Bus' : 'Add New Bus'}</h3>
          <button className="modal-close" onClick={() => setShowBusModal(false)}>×</button>
        </div>
        <form onSubmit={handleBusSubmit} className="modal-body">
          <div className="form-group">
            <label>License Plate *</label>
            <input
              type="text"
              value={busFormData.license_plate}
              onChange={(e) => setBusFormData(prev => ({ ...prev, license_plate: e.target.value }))}
              required
            />
          </div>
          <div className="form-group">
            <label>Model *</label>
            <input
              type="text"
              value={busFormData.model}
              onChange={(e) => setBusFormData(prev => ({ ...prev, model: e.target.value }))}
              required
            />
          </div>
          <div className="form-group">
            <label>Capacity *</label>
            <input
              type="number"
              value={busFormData.capacity}
              onChange={(e) => setBusFormData(prev => ({ ...prev, capacity: e.target.value }))}
              min="1"
              max="100"
              required
            />
          </div>
          <div className="form-group">
            <label>Amenities</label>
            <div className="amenities-grid">
              {['WiFi', 'AC', 'USB Charging', 'Entertainment', 'Reclining Seats', 'Restroom'].map(amenity => (
                <label key={amenity} className="amenity-checkbox">
                  <input
                    type="checkbox"
                    checked={busFormData.amenities.includes(amenity)}
                    onChange={() => handleAmenityChange(amenity)}
                  />
                  {amenity}
                </label>
              ))}
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" onClick={() => setShowBusModal(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">
              {selectedBus ? 'Update' : 'Create'} Bus
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const BusCard = ({ bus }) => (
    <div className="fleet-card">
      <div className="card-header">
        <h4>{bus.license_plate}</h4>
        <span className={`status-badge status-${bus.is_active ? 'active' : 'inactive'}`}>
          {bus.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>
      <div className="card-body">
        <p><strong>Model:</strong> {bus.model}</p>
        <p><strong>Capacity:</strong> {bus.capacity} seats</p>
        <p><strong>Current Trip:</strong> {bus.current_trip || 'Not assigned'}</p>
        <div className="amenities">
          <strong>Amenities:</strong>
          <div className="amenity-tags">
            {bus.amenities?.map(amenity => (
              <span key={amenity} className="amenity-tag">{amenity}</span>
            )) || <span>None</span>}
          </div>
        </div>
      </div>
      <div className="card-actions">
        <button className="btn btn-sm btn-info" onClick={() => handleEditBus(bus)}>
          Edit
        </button>
        <button className="btn btn-sm btn-warning">
          {bus.is_active ? 'Deactivate' : 'Activate'}
        </button>
        <button className="btn btn-sm btn-primary">
          View Trips
        </button>
      </div>
    </div>
  );

  const DriverCard = ({ driver }) => (
    <div className="fleet-card">
      <div className="card-header">
        <h4>{driver.first_name} {driver.last_name}</h4>
        <span className={`status-badge status-${driver.status}`}>
          {driver.status}
        </span>
      </div>
      <div className="card-body">
        <p><strong>Email:</strong> {driver.email}</p>
        <p><strong>Phone:</strong> {driver.phone}</p>
        <p><strong>License:</strong> {driver.license_number}</p>
        <p><strong>Experience:</strong> {driver.years_experience} years</p>
        <p><strong>Current Assignment:</strong> {driver.current_bus || 'Not assigned'}</p>
        <div className="driver-stats">
          <div className="stat">
            <span className="stat-value">{driver.total_trips || 0}</span>
            <span className="stat-label">Total Trips</span>
          </div>
          <div className="stat">
            <span className="stat-value">{driver.avg_rating || 'N/A'}</span>
            <span className="stat-label">Rating</span>
          </div>
        </div>
      </div>
      <div className="card-actions">
        <button className="btn btn-sm btn-info">
          View Profile
        </button>
        <button className="btn btn-sm btn-primary">
          Assign Bus
        </button>
        <button className="btn btn-sm btn-warning">
          View Schedule
        </button>
      </div>
    </div>
  );

  return (
    <div className="fleet-management">
      <div className="page-header">
        <h2>Fleet Management</h2>
        <div className="header-actions">
          {activeTab === 'buses' && (
            <button 
              className="btn btn-primary"
              onClick={() => {
                setSelectedBus(null);
                setBusFormData({ license_plate: '', model: '', capacity: '', amenities: [] });
                setShowBusModal(true);
              }}
            >
              Add New Bus
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'buses' ? 'active' : ''}`}
          onClick={() => setActiveTab('buses')}
        >
          Buses ({busesData?.total || 0})
        </button>
        <button 
          className={`tab ${activeTab === 'drivers' ? 'active' : ''}`}
          onClick={() => setActiveTab('drivers')}
        >
          Drivers ({driversData?.total || 0})
        </button>
      </div>

      {/* Content */}
      <div className="tab-content">
        {activeTab === 'buses' && (
          <div className="buses-section">
            {busesLoading ? (
              <div className="loading">Loading buses...</div>
            ) : (
              <div className="fleet-grid">
                {busesData?.buses?.length > 0 ? (
                  busesData.buses.map(bus => (
                    <BusCard key={bus.id} bus={bus} />
                  ))
                ) : (
                  <p>No buses found</p>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'drivers' && (
          <div className="drivers-section">
            {driversLoading ? (
              <div className="loading">Loading drivers...</div>
            ) : (
              <div className="fleet-grid">
                {driversData?.drivers?.length > 0 ? (
                  driversData.drivers.map(driver => (
                    <DriverCard key={driver.id} driver={driver} />
                  ))
                ) : (
                  <p>No drivers found</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bus Modal */}
      {showBusModal && <BusModal />}
    </div>
  );
};

export default FleetManagement;