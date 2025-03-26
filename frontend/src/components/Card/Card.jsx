
import './Card.css';
const Card =({width=18, title, content}) =>{
    return(
        <div className="card" style={{width: `${width}rem;`}}>
                <div className="card-body">
                  <h6 className="card-subtitle mb-2 text-body-secondary">{title}</h6>
                  <h5 className="card-text">{content}</h5>
                  {/* <p className="card-text">{content}</p>
                  <a href="#" className="card-link">Card link</a>
                  <a href="#" className="card-link">Another link</a> */}
                </div>
              </div>
    )
}
export default Card;