import Button from "../Button/Button";
import { FormCheckBox, FormInput } from "../Form/FormInput";

const Login = ({btnText ='Sign In'})=>{
    return(
        <form className="p-3 p-md-4 bg-transparent">
            <FormInput type="email" label="Email address" placeholder="name@example.com" className={' mb-3'}/>
            <div class="form-floating mb-3">
                <input type="password" className="form-control" id="floatingPassword" placeholder="Password" />
                <label for="floatingPassword">Password</label>
            </div>
            <FormCheckBox value="remember-me" label={'Remember me'} className={' mb-3'}/>
            <Button type="submit" className='w-100'>{btnText}</Button>
            <hr className="my-4"/>
            <small class="text-muted">forgetten password click. <a href="#">SignUp</a></small>
        </form>
    )
}
export default Login;