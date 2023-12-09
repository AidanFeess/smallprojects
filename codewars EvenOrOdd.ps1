function Get-EvenOrOdd($number) {
    If ($number%2 -eq 0){
      return 'Even'
    }
    Else{
      return 'Odd'
    }
  }