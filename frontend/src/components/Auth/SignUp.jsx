import Button from "../Button/Button";
import { FormCheckBox, FormInput } from "../Form/FormInput";

const SignUp = ({btnText = 'Sign Up'}) => {
    return (
        <form className="p-3 p-md-4 bg-transparent">
            {/* Name Input */}
            <FormInput type="text" label="Full Name" placeholder="John Doe" className="mb-3" />
            
            {/* Email Input */}
            <FormInput type="email" label="Email address" placeholder="name@example.com" className="mb-3" />
            
            {/* Password Input */}
            <div className="form-floating mb-3">
                <input type="password" className="form-control" id="floatingPassword" placeholder="Password" />
                <label htmlFor="floatingPassword">Password</label>
            </div>

            {/* Confirm Password Input */}
            <div className="form-floating mb-3">
                <input type="password" className="form-control" id="floatingConfirmPassword" placeholder="Confirm Password" />
                <label htmlFor="floatingConfirmPassword">Confirm Password</label>
            </div>
            
            {/* Terms and Conditions Checkbox */}
            <FormCheckBox value="agree-terms" label="I agree to the terms and conditions" className="mb-3" />
            
            {/* Submit Button */}
            <Button type="submit" className="w-100">{btnText}</Button>
            
            <hr className="my-4" />
            
            {/* Optional small text */}
            <small className="text-muted">
                By clicking {btnText}, you agree to the terms of use.
            </small>
        </form>
    );
}

export default SignUp;
