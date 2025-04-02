import React, { useState } from 'react';
import { FormInput, FormRadioButton, FormCheckBox } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';

const Security = ({ isLoggedIn, user }) => {
    const [loading, setLoading] = useState(false);

    // State for the password change form
    const [passwords, setPasswords] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    // State for privacy settings
    const [privacySetting, setPrivacySetting] = useState('public');

    // State for data sharing settings
    const [dataSharing, setDataSharing] = useState('yes');

    // State for two-factor authentication
    const [twoFactor, setTwoFactor] = useState('on');
    const [smsNumber, setSmsNumber] = useState('555-123-4567');

    // Handle input changes for form fields
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setPasswords((prevState) => ({
            ...prevState,
            [name]: value
        }));
    };

    const handlePrivacyChange = (e) => setPrivacySetting(e.target.value);
    const handleDataSharingChange = (e) => setDataSharing(e.target.value);
    const handleTwoFactorChange = (e) => setTwoFactor(e.target.value);
    const handleSmsNumberChange = (e) => setSmsNumber(e.target.value);

    // Handle form submission for saving password
    const handleSavePassword = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            // Call API to update password here
            console.log('Saving password...', passwords);
            // Simulate API call with a delay
            await new Promise((resolve) => setTimeout(resolve, 1000));
            alert('Password updated successfully!');
        } catch (error) {
            console.error('Error saving password:', error);
        } finally {
            setLoading(false);
        }
    };

    // Handle saving security preferences
    const handleSaveSecurityPreferences = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            // Call API to save security preferences here
            console.log('Saving security preferences...', {
                privacySetting,
                dataSharing,
                twoFactor,
                smsNumber
            });
            // Simulate API call with a delay
            await new Promise((resolve) => setTimeout(resolve, 1000));
            alert('Security preferences saved successfully!');
        } catch (error) {
            console.error('Error saving preferences:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container-xl px-4 mt-4">
            <hr className="mt-0 mb-4" />
            <div className="row">
                <div className="col-lg-8">
                    <div className="card mb-4">
                        <div className="card-header">Change Password</div>
                        <div className="card-body text-body-secondary">
                            <form onSubmit={handleSavePassword}>
                                <div className="mb-3">
                                    <FormInput
                                        label="Current Password"
                                        id="currentPassword"
                                        name="currentPassword"
                                        type="password"
                                        placeholder="Enter current password"
                                        value={passwords.currentPassword}
                                        onChange={handleInputChange}
                                    />
                                </div>
                                <div className="mb-3">
                                    <FormInput
                                        label="New Password"
                                        id="newPassword"
                                        name="newPassword"
                                        type="password"
                                        placeholder="Enter new password"
                                        value={passwords.newPassword}
                                        onChange={handleInputChange}
                                    />
                                </div>
                                <div className="mb-3">
                                    <FormInput
                                        label="Confirm Password"
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        type="password"
                                        placeholder="Confirm new password"
                                        value={passwords.confirmPassword}
                                        onChange={handleInputChange}
                                    />
                                </div>
                                <Button type="submit" loading={loading}>
                                    {loading ? 'Saving...' : 'Save Password'}
                                </Button>
                            </form>
                        </div>
                    </div>
                    <div className="card mb-4">
                        <div className="card-header">Security Preferences</div>
                        <div className="card-body text-body-secondary">
                            <h5 className="mb-1">Account Privacy</h5>
                            <p className="small text-body-secondary">
                                By setting your account to private, your profile information and posts will not be visible to users outside of your user groups.
                            </p>
                            <div className="form-check">
                                <FormRadioButton
                                    label="Public (posts are available to all users)"
                                    id="radioPrivacy1"
                                    name="privacySetting"
                                    value="public"
                                    checked={privacySetting === 'public'}
                                    onChange={handlePrivacyChange}
                                />
                            </div>
                            <div className="form-check">
                                <FormRadioButton
                                    label="Private (posts are available to only users in your groups)"
                                    id="radioPrivacy2"
                                    name="privacySetting"
                                    value="private"
                                    checked={privacySetting === 'private'}
                                    onChange={handlePrivacyChange}
                                />
                            </div>

                            <hr className="my-4" />
                            <h5 className="mb-1">Data Sharing</h5>
                            <p className="small text-body-secondary">
                                Sharing usage data can help us to improve our products and better serve our users as they navigate through our application.
                            </p>
                            <div className="form-check">
                                <FormRadioButton
                                    label="Yes, share data and crash reports with app developers"
                                    id="radioUsage1"
                                    name="dataSharing"
                                    value="yes"
                                    checked={dataSharing === 'yes'}
                                    onChange={handleDataSharingChange}
                                />
                            </div>
                            <div className="form-check">
                                <FormRadioButton
                                    label="No, limit my data sharing with app developers"
                                    id="radioUsage2"
                                    name="dataSharing"
                                    value="no"
                                    checked={dataSharing === 'no'}
                                    onChange={handleDataSharingChange}
                                />
                            </div>
                        </div>
                    </div>
                </div>
                <div className="col-lg-4">
                    <div className="card mb-4">
                        <div className="card-header">Two-Factor Authentication</div>
                        <div className="card-body text-body-secondary">
                            <p>
                                Add another level of security to your account by enabling two-factor authentication. We will send you a text message to verify your login attempts on unrecognized devices and browsers.
                            </p>
                            <div className="form-check">
                                <FormRadioButton
                                    label="On"
                                    id="twoFactorOn"
                                    name="twoFactor"
                                    value="on"
                                    checked={twoFactor === 'on'}
                                    onChange={handleTwoFactorChange}
                                />
                            </div>
                            <div className="form-check">
                                <FormRadioButton
                                    label="Off"
                                    id="twoFactorOff"
                                    name="twoFactor"
                                    value="off"
                                    checked={twoFactor === 'off'}
                                    onChange={handleTwoFactorChange}
                                />
                            </div>
                            {twoFactor === 'on' && (
                                <div className="mt-3">
                                    <FormInput
                                        label="SMS Number"
                                        id="twoFactorSMS"
                                        type="tel"
                                        placeholder="Enter a phone number"
                                        value={smsNumber}
                                        onChange={handleSmsNumberChange}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="card mb-4">
                        <div className="card-header">Delete Account</div>
                        <div className="card-body text-body-secondary">
                            <p>Deleting your account is a permanent action and cannot be undone. If you are sure you want to delete your account, select the button below.</p>
                            <Button variant="danger">
                                I understand, delete my account
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Security;
