function New-PhoneNumber([int[]]$numbers)
{
    $pn = '('+$numbers[0].ToString()+$numbers[1].ToString()+$numbers[2].ToString()+')'
    $pn += ' ' +$numbers[3].ToString()+$numbers[4].ToString()+$numbers[5].ToString()+'-'
    $pn += $numbers[6].ToString()+$numbers[7].ToString()+$numbers[8].ToString()+$numbers[9].ToString()

    return $pn
}