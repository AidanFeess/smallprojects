function accum($s)
{
    $str = ''
    for(($i=0); $i -lt $s.length; $i++){
        for(($x=0); $x -le $i; $x++){
            $l = [string]$s[$i]
            if($x -eq 0){
                $l = $l.ToUpper()
                $str += $l
            }else {
                $str += $l
            }
        }
        if($i -ne $s.length-1){
            $str += '-'
        }else{
            continue
        }
        
    }
    return $str
}