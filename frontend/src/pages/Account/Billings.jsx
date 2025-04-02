import React, { useState } from 'react';
import { FormInput, FormSelect } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Avatar from '../../components/Avatar/Avatar';
import { Icon } from '@iconify/react';
import Table from '../../components/Table/Table';
import axios from 'axios';

const Billings = ({ isLoggedIn, user }) => {
    const [edit, setEdit] = useState(false);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        currentBill: "$20.00",
        nextPaymentDue: "July 15",
        currentPlan: "Freelancer",
        paymentMethods: [
            {
                type: 'Visa',
                icon: <Icon icon="flowbite:visa-solid" width="25" height="24" />,
                lastDigits: '1234',
                expiry: '04/2024',
                isDefault: true,
            },
            {
                type: 'Master Card',
                icon: <Icon icon="logos:mastercard" width="25" height="19" />,
                lastDigits: '5678',
                expiry: '05/2022',
                isDefault: false,
            },
            {
                type: 'American Express',
                icon: <Icon icon="fontisto:american-express" width="25" height="24" />,
                lastDigits: '9012',
                expiry: '01/2026',
                isDefault: false,
            },
        ]
    });

    // Handle form data update
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            // Assuming you have an API endpoint for updating billing info
            await axios.post('/api/update-billing', formData);
            console.log("Billing details updated:", formData);
            setEdit(false);  // Disable edit mode after submitting
        } catch (error) {
            console.error('Error updating billing:', error);
        } finally {
            setLoading(false);
        }
    };

    // Handle adding a payment method
    const handleAddPaymentMethod = async () => {
        setLoading(true);
        try {
            // Example of an API request to add a payment method
            const newPaymentMethod = {
                type: 'New Card Type',
                lastDigits: '0000',
                expiry: '01/2027',
            };
            // const response = await axios.post('/api/add-payment-method', newPaymentMethod);
            // setFormData((prevState) => ({
            //     ...prevState,
            //     paymentMethods: [...prevState.paymentMethods, response.data],
            // }));
        } catch (error) {
            console.error('Error adding payment method:', error);
        } finally {
            setLoading(false);
        }
    };

    // Handle setting a payment method as default
    const handleMakeDefault = async (methodIndex) => {
        setLoading(true);
        try {
            // Assuming you have an API endpoint to set the default payment method
            const updatedPaymentMethods = formData.paymentMethods.map((method, index) => {
                if (index === methodIndex) {
                    method.isDefault = true;
                } else {
                    method.isDefault = false;
                }
                return method;
            });
            setFormData({
                ...formData,
                paymentMethods: updatedPaymentMethods
            });

            // await axios.post('/api/set-default-payment', {
            //     methodId: formData.paymentMethods[methodIndex].id, // Assuming there's an ID
            // });
        } catch (error) {
            console.error('Error making payment method default:', error);
        } finally {
            setLoading(false);
        }
    };

    // Example headers for the billing history table
    const headers = ['Transaction ID', 'Date', 'Amount', 'Status'];

    // Example transaction data
    const billingHistory = [
        {
            transactionId: '#39201',
            date: '06/15/2021',
            amount: '$29.99',
            status: 'Pending',
        },
        {
            transactionId: '#38594',
            date: '05/15/2021',
            amount: '$29.99',
            status: 'Paid',
        },
        {
            transactionId: '#38223',
            date: '04/15/2021',
            amount: '$29.99',
            status: 'Paid',
        },
        {
            transactionId: '#38125',
            date: '03/15/2021',
            amount: '$29.99',
            status: 'Paid',
        },
    ];

    return (
        <div className="container-fluid px-4 mt-4">
            <div className="card-header d-flex justify-content-between">
                Billing Details
                <span className="ms-auto">
                    <Icon icon="mage:edit" width="24" height="24" onClick={() => setEdit(!edit)} />
                </span>
            </div>
            <hr className="mt-0 mb-4" />

            <form onSubmit={handleSubmit}>
                <div className="row">
                    <div className="col-lg-4 mb-4">
                        <div className="card h-100 border-start-lg border-start-primary">
                            <div className="card-body text-dark">
                                <div className="small text-body-secondary">Current monthly bill</div>
                                <div className="h3">
                                    {edit ? (
                                        <FormInput
                                            name="currentBill"
                                            value={formData.currentBill}
                                            onChange={handleInputChange}
                                        />
                                    ) : (
                                        formData.currentBill
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="col-lg-4 mb-4">
                        <div className="card h-100 border-start-lg border-start-secondary">
                            <div className="card-body text-dark">
                                <div className="small text-body-secondary">Next payment due</div>
                                <div className="h3">
                                    {edit ? (
                                        <FormInput
                                            name="nextPaymentDue"
                                            value={formData.nextPaymentDue}
                                            onChange={handleInputChange}
                                        />
                                    ) : (
                                        formData.nextPaymentDue
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="col-lg-4 mb-4">
                        <div className="card h-100 border-start-lg border-start-success">
                            <div className="card-body text-dark">
                                <div className="small text-body-secondary">Current plan</div>
                                <div className="h3 d-flex align-items-center">
                                    {edit ? (
                                        <FormInput
                                            name="currentPlan"
                                            value={formData.currentPlan}
                                            onChange={handleInputChange}
                                        />
                                    ) : (
                                        formData.currentPlan
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="card card-header-actions mb-4">
                    <div className="card-header d-flex align-items-center justify-content-between">
                        Payment Methods
                        <span>
                            <Button onClick={handleAddPaymentMethod}>Add Payment Method</Button>
                        </span>
                    </div>
                    <div className="card-body px-0 text-body-secondary">
                        {formData.paymentMethods.map((method, index) => (
                            <div key={index} className={`d-flex align-items-center justify-content-between px-4 py-2 mb-2 ${index === formData.paymentMethods.length - 1 ? '' : 'border-bottom'}`}>
                                <div className="d-flex align-items-center">
                                    {method.icon}
                                    <div className="ms-4 text-body-secondary">
                                        <div className="small">{`${method.type} ending in ${method.lastDigits}`}</div>
                                        <div className="text-xs text-body-secondary">Expires {method.expiry}</div>
                                    </div>
                                </div>
                                <div className="ms-4 small">
                                    {method.isDefault ? (
                                        <div className="badge bg-primary text-dark">Default</div>
                                    ) : (
                                        <Button outline onClick={() => handleMakeDefault(index)}>Make Default</Button>
                                    )}
                                    <Button outline variant="secondary" className="ms-2">Edit</Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="card mb-4">
                    <div className="card-header">Billing History</div>
                    <div className="card-body text-dark p-0">
                        <Table headers={headers} data={billingHistory} className='table-billing-history' />
                    </div>
                </div>

                {edit && (
                    <Button type="submit" loading={loading}>{loading ? 'Saving ...' : 'Save changes'}</Button>
                )}
            </form>
        </div>
    );
};

export default Billings;
