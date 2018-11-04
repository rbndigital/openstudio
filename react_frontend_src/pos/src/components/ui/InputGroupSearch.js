import React from "react"


const InputGroupSearch = ({value, placeholder, onChange=f=>f, onClear=f=>f}) => 
    <div className="input-group">
        <span className="input-group-addon">
            <i className="fa fa-search"></i>
        </span>
        <input type="text"
               id="InputSearch"
               value={value}
               className="form-control"
               placeholder={placeholder} 
               onChange={onChange}
               ref={input => input && input.focus()} />
        <span className="input-group-addon" onClick={onClear}>
            <i className="fa fa-times"></i>
        </span>
    </div>


export default InputGroupSearch