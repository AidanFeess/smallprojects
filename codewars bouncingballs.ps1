function bouncing-ball{
    [OutputType([int])]
    Param ([double]$h, [double]$bounce, [double]$window)

    $ttl = 0

    if($h -gt 0 -And $bounce -gt 0 -And $bounce -lt 1 -And $window -lt $h){
        while ($h -gt $window) {
            $ttl += 1
            $h *= $bounce
            if($h -gt $window){
                $ttl += 1
            }
        }
        return $ttl
    }
    else{
        return -1
    }
}