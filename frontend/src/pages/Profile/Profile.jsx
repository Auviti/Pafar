import React, { useState, useEffect } from 'react';
import ThemeProvider from '../../utils/ThemeProvider';
import { FormInput } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Pagination from '../../components/Pagination/Pagination';

const Profile = ({ header, footer, bottomheader }) => {
  // Array representing the card data with actual image URLs
  const cards = Array.from({ length: 35 }, (_, index) => ({
    title: `Thumbnail ${index + 1}`,
    description: 'This is a wider card with supporting text below as a natural lead-in to additional content. This content is a little bit longer.',
    time: '9 mins',
    imageUrl: `https://picsum.photos/seed/${index}/225/225`, // Example placeholder image URL, with seed to generate different images
  }));

  // State for pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);  // Number of items per page (this can be adjusted)
  

  // Get the current cards to display based on the page number and items per page
  const currentCards = cards.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Handle page selection from pagination
  const handlePageSelect = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

    return (
        <ThemeProvider>
            {header}
            <div className="container-fluid" style={{ height: '50px' }}></div>
            <div class="container-xl px-4 mt-4">
                <nav class="nav nav-borders">
                    <a class="nav-link active ms-0" href="https://www.bootdey.com/snippets/view/bs5-edit-profile-account-details" target="__blank">Profile</a>
                    <a class="nav-link" href="https://www.bootdey.com/snippets/view/bs5-profile-billing-page" target="__blank">Billing</a>
                    <a class="nav-link" href="https://www.bootdey.com/snippets/view/bs5-profile-security-page" target="__blank">Security</a>
                    <a class="nav-link" href="https://www.bootdey.com/snippets/view/bs5-edit-notifications-page"  target="__blank">Notifications</a>
                </nav>
                <hr class="mt-0 mb-4"/>
                <div class="row">
                    <div class="col-xl-4">
                        <div class="card mb-4 mb-xl-0">
                            <div class="card-header">Profile Picture</div>
                            <div class="card-body text-center">
                                <img class="img-account-profile rounded-circle mb-2" src="http://bootdey.com/img/Content/avatar/avatar1.png" alt="" />
                                <div class="small font-italic text-muted mb-4">JPG or PNG no larger than 5 MB</div>
                                 <Button type="button" >Upload new image</Button>
                            </div>
                        </div>
                    </div>
                    <div class="col-xl-8">
                        <div class="card mb-4">
                            <div class="card-header">Account Details</div>
                            <div class="card-body">
                                <form>
                                    <div class="mb-3">
                                        <label class="small mb-1" for="inputUsername">Username (how your name will appear to other users on the site)</label>
                                        <input class="form-control" id="inputUsername" type="text" placeholder="Enter your username" value="username"/>
                                    </div>
                                    <div class="row gx-3 mb-3">
                                        <div class="col-md-6">
                                            <label class="small mb-1" for="inputFirstName">First name</label>
                                            <input class="form-control" id="inputFirstName" type="text" placeholder="Enter your first name" value="Valerie/"/>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="small mb-1" for="inputLastName">Last name</label>
                                            <input class="form-control" id="inputLastName" type="text" placeholder="Enter your last name" value="Luna"/>
                                        </div>
                                    </div>
                                    <div class="row gx-3 mb-3">
                                        <div class="col-md-6">
                                            <label class="small mb-1" for="inputOrgName">Organization name</label>
                                            <input class="form-control" id="inputOrgName" type="text" placeholder="Enter your organization name" value="Start Bootstrap"/>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="small mb-1" for="inputLocation">Location</label>
                                            <input class="form-control" id="inputLocation" type="text" placeholder="Enter your location" value="San Francisco, CA"/>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="small mb-1" for="inputEmailAddress">Email address</label>
                                        <input class="form-control" id="inputEmailAddress" type="email" placeholder="Enter your email address" value="name@example.com"/>
                                    </div>
                                    <div class="row gx-3 mb-3">
                                        <div class="col-md-6">
                                            <FormInput id="inputPhone" forId="inputPhone" label={'Phone number'} type="tel" placeholder="Enter your phone number" value="555-123-4567"/>
                                        </div>
                                        <div class="col-md-6">
                                            <FormInput id="inputBirthday" forId="inputBirthday" label={'Birthday'} type="text" placeholder="Enter your birthday" value="06/10/1988"/>
                                        </div>
                                    </div>
                                    <Button type="button">Save changes</Button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {footer}
            {bottomheader}
        </ThemeProvider>
    );
};

export default Profile;
