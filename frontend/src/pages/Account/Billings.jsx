import React, { useState, useEffect } from 'react';
import { FormInput, FormSelect } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Avatar from '../../components/Avatar/Avatar';

const Billings = ({ isLoggedIn, user, }) => {
    // Array representing the card data with actual image URLs
    const [edit, setEdit] = useState(false);
    
    
    return (
        <div class="container-fluid px-4 mt-4">
            <hr class="mt-0 mb-4"/>
            <div class="row">
                <div class="col-lg-4 mb-4">
                    <div class="card h-100 border-start-lg border-start-primary">
                        <div class="card-body text-dark">
                            <div class="small text-body-secondary">Current monthly bill</div>
                            <div class="h3">$20.00</div>
                            <a class="text-arrow-icon small" href="#!">
                                Switch to yearly billing
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-arrow-right"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                            </a>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4 mb-4">
                    <div class="card h-100 border-start-lg border-start-secondary">
                        <div class="card-body text-dark">
                            <div class="small text-body-secondary">Next payment due</div>
                            <div class="h3">July 15</div>
                            <a class="text-arrow-icon small text-secondary" href="#!">
                                View payment history
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-arrow-right"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                            </a>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4 mb-4">
                    <div class="card h-100 border-start-lg border-start-success">
                        <div class="card-body text-dark">
                            <div class="small text-body-secondary">Current plan</div>
                            <div class="h3 d-flex align-items-center">Freelancer</div>
                            <a class="text-arrow-icon small text-success" href="#!">
                                Upgrade plan
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-arrow-right"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card card-header-actions mb-4">
                <div class="card-header d-flex align-items-center justify-content-between">
                    Payment Methods
                    <span><Button>Add Payment Method</Button></span>
                    
                </div>
                <div class="card-body px-0">
                    <div class="d-flex align-items-center justify-content-between px-4">
                        <div class="d-flex align-items-center">
                            <i class="fab fa-cc-visa fa-2x cc-color-visa"></i>
                            <div class="ms-4  text-body-secondary">
                                <div class="small">Visa ending in 1234</div>
                                <div class="text-xs  text-body-secondary">Expires 04/2024</div>
                            </div>
                        </div>
                        <div class="ms-4 small">
                            <div class="badge bg-primary text-dark">Default</div>
                            <Button outline variant='secondary' className={'ms-2'}>Edit</Button>
                        </div>
                    </div>
                    <hr />
                    <div class="d-flex align-items-center justify-content-between px-4">
                        <div class="d-flex align-items-center">
                            <i class="fab fa-cc-mastercard fa-2x cc-color-mastercard"></i>
                            <div class="ms-4  text-body-secondary">
                                <div class="small">Mastercard ending in 5678</div>
                                <div class="text-xs text-body-secondary">Expires 05/2022</div>
                            </div>
                        </div>
                        <div class="ms-4 small">
                            <Button outline >Make Default</Button>
                            <Button outline variant='secondary' className={'ms-2'}>Edit</Button>
                        </div>
                    </div>
                    <hr />
                    <div class="d-flex align-items-center justify-content-between px-4">
                        <div class="d-flex align-items-center">
                            <i class="fab fa-cc-amex fa-2x cc-color-amex"></i>
                            <div class="ms-4 text-body-secondary">
                                <div class="small">American Express ending in 9012</div>
                                <div class="text-xs text-body-secondary">Expires 01/2026</div>
                            </div>
                        </div>
                        <div class="ms-4 small">
                            <Button outline >Make Default</Button>
                            <Button outline variant='secondary' className={'ms-2'}>Edit</Button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card mb-4">
                <div class="card-header">Billing History</div>
                <div class="card-body text-dark p-0">
                    <div class="table-responsive table-billing-history">
                        <table class="table mb-0">
                            <thead>
                                <tr>
                                    <th class="border-gray-200" scope="col">Transaction ID</th>
                                    <th class="border-gray-200" scope="col">Date</th>
                                    <th class="border-gray-200" scope="col">Amount</th>
                                    <th class="border-gray-200" scope="col">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>#39201</td>
                                    <td>06/15/2021</td>
                                    <td>$29.99</td>
                                    <td><span class="badge bg-light text-dark">Pending</span></td>
                                </tr>
                                <tr>
                                    <td>#38594</td>
                                    <td>05/15/2021</td>
                                    <td>$29.99</td>
                                    <td><span class="badge bg-success">Paid</span></td>
                                </tr>
                                <tr>
                                    <td>#38223</td>
                                    <td>04/15/2021</td>
                                    <td>$29.99</td>
                                    <td><span class="badge bg-success">Paid</span></td>
                                </tr>
                                <tr>
                                    <td>#38125</td>
                                    <td>03/15/2021</td>
                                    <td>$29.99</td>
                                    <td><span class="badge bg-success">Paid</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        );
};

export default Billings;
