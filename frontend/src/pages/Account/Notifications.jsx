import React, { useState, useEffect } from 'react';
import { FormInput, FormCheckBox, FormToggle } from '../../components/Form/FormInput'; // Custom components
import Button from '../../components/Button/Button'; // Custom Button
import Avatar from '../../components/Avatar/Avatar'; // Custom Avatar

const Notifications = ({ isLoggedIn, user }) => {
    const [edit, setEdit] = useState(false);

    return (
        <>
            <hr className="mt-0 mb-4" />
            <div className="row">
                <div className="col-lg-8">
                    {/* Email Notifications */}
                    <div className="card card-header-actions mb-4">
                        <div className="card-header">
                            Email Notifications
                            <FormCheckBox id="flexSwitchCheckChecked" checked />
                        </div>
                        <div className="card-body text-body-secondary">
                            <form>
                                <div className="mb-3">
                                    <label className="small mb-1" htmlFor="inputNotificationEmail">
                                        Default notification email
                                    </label>
                                    <FormInput
                                        id="inputNotificationEmail"
                                        type="email"
                                        value="name@example.com"
                                        disabled
                                    />
                                </div>
                                <div className="mb-0">
                                    <label className="small mb-2">
                                        Choose which types of email updates you receive
                                    </label>
                                    <FormCheckBox
                                        id="checkBookingConfirmation"
                                        label="Booking Confirmation"
                                        checked
                                    />
                                    <FormCheckBox
                                        id="checkBookingReminder"
                                        label="Booking Reminder"
                                        checked
                                    />
                                    <FormCheckBox
                                        id="checkBookingCancellation"
                                        label="Booking Cancellation"
                                    />
                                    <FormCheckBox
                                        id="checkPromotionalOffers"
                                        label="Special Offers and Discounts"
                                    />
                                    <FormCheckBox
                                        id="checkSecurity"
                                        label="Security Alerts"
                                        checked
                                        disabled
                                    />
                                </div>
                            </form>
                        </div>
                    </div>

                    {/* Push Notifications */}
                    <div className="card card-header-actions mb-4">
                        <div className="card-header">
                            Push Notifications
                            <FormCheckBox id="smsToggleSwitch" checked />
                            
                        </div>
                        <div className="card-body text-body-secondary">
                            <form>
                                <div className="mb-3">
                                    <label className="small mb-1" htmlFor="inputNotificationSms">
                                        Default SMS number
                                    </label>
                                    <FormInput
                                        id="inputNotificationSms"
                                        type="tel"
                                        value="123-456-7890"
                                        disabled
                                    />
                                </div>
                                <div className="mb-0">
                                    <label className="small mb-2">
                                        Choose which types of push notifications you receive
                                    </label>
                                    <FormCheckBox
                                        id="checkSmsBookingConfirmation"
                                        label="Booking Confirmation"
                                        checked
                                    />
                                    <FormCheckBox
                                        id="checkSmsBookingReminder"
                                        label="Booking Reminder"
                                    />
                                    <FormCheckBox
                                        id="checkSmsBookingUpdate"
                                        label="Booking Updates"
                                    />
                                    <FormCheckBox
                                        id="checkSmsBookingCancellation"
                                        label="Booking Cancellation"
                                    />
                                    <FormCheckBox
                                        id="checkSmsPrivateMessage"
                                        label="You receive a private message"
                                        checked
                                    />
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                {/* Notification Preferences */}
                <div className="col-lg-4">
                    <div className="card">
                        <div className="card-header">Notification Preferences</div>
                        <div className="card-body text-body-secondary">
                            <form>
                                <FormCheckBox
                                    id="checkAutoSubscribeBookingUpdates"
                                    label="Automatically subscribe to booking updates"
                                    checked
                                />
                                <FormCheckBox
                                    id="checkAutoSubscribePromotions"
                                    label="Automatically subscribe to special offers and promotions"
                                />
                                <Button variant='danger'>
                                    Unsubscribe from all notifications
                                </Button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Notifications;
