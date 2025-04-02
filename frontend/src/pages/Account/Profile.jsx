import React, { useState, useEffect } from 'react';
import { FormInput, FormSelect } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Avatar from '../../components/Avatar/Avatar';
import { Icon } from '@iconify/react';
const Profile = ({ isLoggedIn, user}) => {
    const [edit, setEdit] = useState(false);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        firstName: user?.firstName || '',
        lastName: user?.lastName || '',
        role: user?.role || '',
        email: user?.email || '',
        active: user?.active || false,
        age: user?.age || '',
        gender: user?.gender || '',
        phone: user?.phone || '',
        birthday: user?.birthday || '',
        profilePic: user?.profilePic || '', // Store the profile picture URL
    });

    const [profilePic, setProfilePic] = useState(null); // State to store the selected profile picture

    // Handle form data updates
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prevData) => ({
            ...prevData,
            [name]: value,
        }));
    };

    // Handle profile picture change
    const handleProfilePicChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setProfilePic(URL.createObjectURL(file)); // Preview the uploaded image
            setFormData((prevData) => ({
                ...prevData,
                profilePic: file, // Store the file itself for later use
            }));
        }
    };

    // Handle form submission
    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true);
        // Here you would handle the form submission, including uploading the new profile picture if it was changed
        console.log('Form data submitted:', formData);
        // If there's an API request to update the user's info, call it here
        // setLoading(false);
    };

    return (
        <div className="row">
            <div className="col-xl-4">
                <div className="card mb-4 mb-xl-0">
                    <div className="card-header">Profile Picture</div>
                    <div className="card-body text-center">
                        <Avatar
                            src={profilePic || formData.profilePic || "http://bootdey.com/img/Content/avatar/avatar1.png"}
                            alt="Profile"
                            size={230}
                            shape="circle"
                        />
                        <div className="small font-italic text-dark mb-4 p-2">
                            {edit ? 'JPG or PNG no larger than 5 MB' : user?.id}
                        </div>
                        {edit && (
                            <>
                                <input
                                    type="file"
                                    className="form-control mb-2"
                                    accept="image/*"
                                    onChange={handleProfilePicChange}
                                />
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="col-xl-8">
                <div className="card mb-4">
                <div className="card-header d-flex justify-content-between">
                        Account Details 
                        <span className="ms-auto"><Icon icon="mage:edit" width="24" height="24" onClick={()=>setEdit(!edit)}/></span>
                </div>

                    <div className="card-body">
                        <form onSubmit={handleSubmit}>
                            <div className="row gx-3">
                                <div className="col-md-6 mb-3">
                                    <FormInput
                                        id="inputFirstName"
                                        name="firstName"
                                        label={'First name'}
                                        type="text"
                                        placeholder="Enter your first name"
                                        value={formData.firstName}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                                <div className="col-md-6 mb-3">
                                    <FormInput
                                        id="inputLastName"
                                        name="lastName"
                                        label={'Last name'}
                                        type="text"
                                        placeholder="Enter your last name"
                                        value={formData.lastName}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                            </div>

                            <div className="row gx-3">
                                <div className="col-md-6 mb-3">
                                    <FormInput
                                        id="inputRole"
                                        name="role"
                                        label={'Role'}
                                        type="text"
                                        value={formData.role}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                                <div className="col-md-6 mb-3">
                                    <FormInput
                                        id="inputEmailAddress"
                                        name="email"
                                        label={'Email address'}
                                        type="email"
                                        placeholder="Enter your email address"
                                        value={formData.email}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                            </div>

                            <div className="mb-3">
                                <FormInput
                                    id="inputActive"
                                    name="active"
                                    label={'Active'}
                                    type="text"
                                    value={formData.active ? "Active" : "Inactive"}
                                    onChange={handleChange}
                                    disabled={!edit}
                                />
                            </div>

                            <div className="row gx-3">
                                <div className="col-md-6 mb-3">
                                    <FormInput
                                        id="inputAge"
                                        name="age"
                                        label={'Age'}
                                        type="number"
                                        value={formData.age}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                                <div className="col-md-6 mb-3">
                                    <FormSelect
                                        id="inputGender"
                                        name="gender"
                                        items={['Male', 'Female']}
                                        label={'Gender'}
                                        value={formData.gender}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                            </div>

                            <div className="row gx-3">
                                <div className="col-md-6 mb-3">
                                    <FormInput
                                        id="inputPhone"
                                        name="phone"
                                        label={'Phone number'}
                                        type="tel"
                                        placeholder="Enter your phone number"
                                        value={formData.phone}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                                <div className="col-md-6 mb-3">
                                    <FormInput
                                        id="inputBirthday"
                                        name="birthday"
                                        label={'Birthday'}
                                        type="date"
                                        value={formData.birthday}
                                        onChange={handleChange}
                                        disabled={!edit}
                                    />
                                </div>
                            </div>

                            <Button type="submit" loading={loading}>{loading?'Saving ...':'Save changes'}</Button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
