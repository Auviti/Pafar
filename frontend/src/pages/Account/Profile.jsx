import React, { useState, useEffect } from 'react';
import { FormInput, FormSelect } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Avatar from '../../components/Avatar/Avatar';

const Profile = ({ isLoggedIn, user, }) => {
    // Array representing the card data with actual image URLs
    const [edit, setEdit] = useState(false);
    
    
    return (
        <div class="row">
            <div class="col-xl-4">
                <div class="card mb-4 mb-xl-0">
                    <div class="card-header">Profile Picture</div>
                    <div class="card-body text-center">
                        <Avatar src="http://bootdey.com/img/Content/avatar/avatar1.png" alt="" size={230} shape='circle'/>
                        <div class="small font-italic text-dark mb-4 p-2">{edit?'JPG or PNG no larger than 5 MB':user?.id}</div>
                        {edit && <Button type="button" >Upload new image</Button>}
                    </div>
                </div>
            </div>
            <div class="col-xl-8">
                <div class="card mb-4">
                    <div class="card-header">Account Details</div>
                    <div class="card-body">
                        <form>
                            <div class="row gx-3">
                                <div class="col-md-6 mb-3">
                                    <FormInput id="inputFirstName" forId="inputFirstName" label={'First name'} type="text" placeholder="Enter your first name" value="Valerie/"/>
                            
                                </div>
                                <div class="col-md-6 mb-3">
                                    <FormInput id="inputLastName" forId="inputLastName" label={'Last name'} type="text" placeholder="Enter your last name" value="Luna"/>
                                </div>
                            </div>
                            <div class="row gx-3">
                                <div class="col-md-6 mb-3">
                                    <FormInput id="inputRole" forId="inputRole" label={'Role'} type="text" value="dfdfdd"/>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <FormInput id="inputEmailAddress" forId="inputEmailAddress" label={'Email address'} type="email" placeholder="Enter your email address" value="name@example.com"/>
                            
                                </div>
                            </div>
                            <div class="mb-3">
                                <FormInput id="inputActive" forId="inputActive" label={'Active'} type="bool" value="Active"/>
                            </div>
                            <div class="row gx-3">
                                <div class="col-md-6 mb-3">
                                    <FormInput id="inputAge" forId="inputAge" label={'Age'} type="int" value="4"/>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <FormSelect id="inputGender" items={['Male', 'Female']} label={'Gender'}/>
                                </div>
                            </div>
                            <div class="row gx-3">
                                <div class="col-md-6 mb-3">
                                    <FormInput id="inputPhone" forId="inputPhone" label={'Phone number'} type="tel" placeholder="Enter your phone number" value="555-123-4567"/>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <FormInput id="inputBirthday" forId="inputBirthday" label={'Birthday'} type="text" placeholder="Enter your birthday" value="06/10/1988"/>
                                </div>
                            </div>
                            <Button>Save changes</Button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
