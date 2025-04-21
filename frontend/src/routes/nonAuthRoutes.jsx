import React from 'react';
import Home from '../pages/Home/Home';
import Account from '../pages/Account/Account';
import Tickets from '../pages/Bookings/Tickets';
import SignUp from '../components/Auth/SignUp';


const NonAuthRoutes = ({ API_URL,Companyname,isLoggedIn,user,header, footer, bottomheader,currentUrl }) => [
  {
    path: "/",
    element: <Home API_URL={API_URL} Companyname={Companyname} isLoggedIn={isLoggedIn} user={user} header={header} footer={footer} bottomheader={bottomheader} />,
    title: "home"
  },
  {
    path: "/tickets",
    element: <Tickets API_URL={API_URL} Companyname={Companyname} isLoggedIn={isLoggedIn} user={user} header={header} footer={footer} bottomheader={bottomheader} />,
    title: "tickets"
  },
  {
    path: "/signup",
    element: <SignUp />,
    title: "signup"
  },
  {
    path: "/accounts/:id/profile",
    element: <Account API_URL={API_URL} Companyname={Companyname} index={0} isLoggedIn={isLoggedIn} currentUrl={currentUrl} user={user} header={header} footer={footer} bottomheader={bottomheader} />,
    title: "profile"
  },
  {
    path: "/accounts/:id/billing",
    element: <Account API_URL={API_URL} Companyname={Companyname} index={1} isLoggedIn={isLoggedIn} currentUrl={currentUrl} user={user} header={header} footer={footer} bottomheader={bottomheader} />,
    title: "billing"
  },
  {
    path: "/accounts/:id/security",
    element: <Account API_URL={API_URL} Companyname={Companyname} index={2} isLoggedIn={isLoggedIn} currentUrl={currentUrl} user={user} header={header} footer={footer} bottomheader={bottomheader} />,
    title: "security"
  },
  {
    path: "/accounts/:id/notifications",
    element: <Account API_URL={API_URL} Companyname={Companyname} index={3} isLoggedIn={isLoggedIn} currentUrl={currentUrl} user={user} header={header} footer={footer} bottomheader={bottomheader} />,
    title: "notifications"
  },
  // {
  //   path: "/about",
  //   element: <About API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "about"
  // },
  // {
  //   path: "/login",
  //   element: <Login API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "login"
  // },
  // {
  //   path: "/logout",
  //   element: <LogoutPage/>,
  //   title: "logout"
  // },
  // {
  //   path: "/login-fingerprint",
  //   element: <Loginfingerprint API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "login-fingerprint"
  // },
  // {
  //   path: "/login-face",
  //   element: <Loginfingerprint API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "login-face"
  // },
  // {
  //   path: "/signup",
  //   element: <Signup API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "signup"
  // },
  // {
  //   path: "/signup-for-suppliers",
  //   element: <SignUpForSuppliers API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "signUpForSuppliers"
  // },
  // {
  //   path: "/verify-email-otp",
  //   element: <VerifyMail API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "verify-email-otp"
  // },
  // {
  //   path: "/verify-email-confirmation",
  //   element: <VerifyMailConfirmation API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "verify-email-confirmation"
  // },
  // {
  //   path: "/forgotpassword",
  //   element: <ForgotPassword API_URL={API_URL} Companyname={Companyname}/>,
  //   title: 'forgotpassword'
  // },
  // {
  //   path: "/passwordreset",
  //   element: <PasswordReset API_URL={API_URL} Companyname={Companyname}/>,
  //   title: 'passwordreset'
  // },
  // {
  //   path: "/shop",
  //   element: <Marketplace API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "shop"
  // },
  // {
  //   path: "/shop/:category",
  //   element: <Categories API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "categories"
  // },
  
  // {
  //   path:"/shop/products/:id",
  //   element:<ProductPage API_URL={API_URL} Companyname={Companyname}/>,
  //   title:'productitem'
  // },
  // {
  //   path: "/map",
  //   element: <Map API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "map"
  // },
  // {
  //   path: "/cart",
  //   element: <Cart API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "cart"
  // },
  // {
  //   path: "/payment/confirmation",
  //   element: <PaymentConfirmation API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "payment"
  // },
  // {
  //   path: "/payment/confirmation/orderresult",
  //   element: <OrderResult API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "orderresult"
  // },
  // {
  //   path: "/payment/order/:id",
  //   element: <TrackingOrder API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "trackingorder"
  // },
  // {
  //   path: "/user",
  //   element: <User API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "user"
  // },
  // {
  //   path: "/user/orders/:id",
  //   element: <User API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "user"
  // },
  // {
  //   path: "/message",
  //   element: <User API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "message"
  // },
  // {
  //   path: "/test",
  //   element: <Test API_URL={API_URL} Companyname={Companyname}/>,
  //   title: "testPage"
  // }, 
];

export default NonAuthRoutes;
