#include "stm32f4xx.h"                 
#include "stm32f429xx.h"
#include <stdint.h>
#include<stdio.h>
#include<string.h>

void SysClockConfig (void);

void I2C_Config (void);
void I2C_Start (void);
void I2C_Write (uint8_t data);
void I2C_Address (uint8_t Address);
void I2C_Stop (void);

void TIM6Config (void);
void Delay_us(uint16_t us);
void Delay_ms(uint16_t ms);
// ----------------------------------------------------------------------------------------------
// Timer configuration function for generating delays required for the program execution
// ----------------------------------------------------------------------------------------------
void TIM6Config (void)
{
	RCC->APB1ENR |= (1<<4);  													// Enable the RCC for TIM6 (General Timer)
	TIM6->PSC = 180-1;  																// 180MHz/180 = 1 MHz ~~ 1 uS delay
	TIM6->ARR = 0xffff;  															// MAX ARR value to generate any delay
	TIM6->CR1 |= (1<<0); 															// Enable the Timer Counter
	while (!(TIM6->SR & (1<<0)));  										// UIF: Update interrupt flag.
}
// ----------------------------------------------------------------------------------------------




// ----------------------------------------------------------------------------------------------
// Timer function for generating delays required in microseconds
// ----------------------------------------------------------------------------------------------
void Delay_us (uint16_t us)
{
	TIM6->CNT = 0;
	while (TIM6->CNT < us);
}
// ----------------------------------------------------------------------------------------------




// ----------------------------------------------------------------------------------------------
// Timer function for generating delays required in milliseconds
// ----------------------------------------------------------------------------------------------
void Delay_ms (uint16_t ms)
{
	for (uint16_t i=0; i<ms; i++)
	{
		Delay_us (1000); 
	}
}

void I2C_Config (void)
{
	// -------------------------------------------------------------------------------------------
	// Configuring RCC Enable clock for GPIO and I2C
	// -------------------------------------------------------------------------------------------
	RCC->APB1ENR |= (1<<21);  									// Enable I2C CLOCK
	RCC->AHB1ENR |= (1<<1);   									// Enable GPIOB CLOCK
	// -------------------------------------------------------------------------------------------
	
	
	
	// -------------------------------------------------------------------------------------------
	// Configure the I2C PINs for ALternate Functions
	// -------------------------------------------------------------------------------------------
	GPIOB->MODER |= (2<<16) | (2<<18);  				// Alternate Function mode for PB8 & xrd
	GPIOB->OTYPER |= (1<<8) | (1<<9);  					// Selecting Open Drain Mode for Both the PINS
	GPIOB->OSPEEDR |= (3<<16) | (3<<18);  				// Selecting High Speed for Both PINS
	GPIOB->PUPDR |= (1<<16) | (1<<18);  				// Pul Up Mode because I2C operate in Pul-up state
	GPIOB->AFR[1] |= (4<<0) | (4<<4); 	 				// Selecting AF4 for PB8 & PB9
	// -------------------------------------------------------------------------------------------
	
	
	
	// -------------------------------------------------------------------------------------------
	// Reseting CR1 and Setting PCLK1 info in CR2 and configuring the Clock Control Registers
	// -------------------------------------------------------------------------------------------
	I2C1->CR1 |= (1<<15);                       					// Reseting CR1 (SWRST bit)
	I2C1->CR1 &= ~(1<<15);											// Reseting CR1
	I2C1->CR2 |= (45<<0);  											// PCLK1 FREQUENCY in MHz
	I2C1->CCR = 225<<0;  											// Check calculation in Report
	I2C1->TRISE = 46;  												// Check Report for calculations
	// -------------------------------------------------------------------------------------------
	I2C1->CR1 |= (1<<0);  											// Enable I2C
	
}




void I2C_Start (void)
{
	// -------------------------------------------------------------------------------------------
	// Enabling the ACK bit and Enable the start bit SB
	// -------------------------------------------------------------------------------------------
	I2C1->CR1 |= (1<<10);  											// Enable the ACK
	I2C1->CR1 |= (1<<8);  											// Generate START
	while (!(I2C1->SR1 & (1<<0)));  								// Wait fror SB(Start Bit) bit to set
	// -------------------------------------------------------------------------------------------
}




void I2C_Write (uint8_t data)
{
	// -------------------------------------------------------------------------------------------
	// Writing the DATA into Data Register if Transmission Register Empty
	// -------------------------------------------------------------------------------------------
	while (!(I2C1->SR1 & (1<<7)));  						// Waiting for TXE bit --> Transmit Register Empty
	I2C1->DR = data;										// Write the Data into DR (Data Register)
	while (!(I2C1->SR1 & (1<<2)));  						// Waiting for BTF bit to set
	// -------------------------------------------------------------------------------------------
}




void I2C_Address (uint8_t Address)
{	
	// -------------------------------------------------------------------------------------------
	// Sending Slave Address & the update is reflected in ADDR bit, finally clear the ADDR
	// -------------------------------------------------------------------------------------------
	I2C1->DR = Address;  									// Sending Address by putting it in Data Register
	while (!(I2C1->SR1 & (1<<1)));  						// Waiting till address is transmitted
	uint8_t temp = I2C1->SR1 | I2C1->SR2;  					// Clear the ADDR by reading SR1 & SR2 (Manual)
	// -------------------------------------------------------------------------------------------
}




void I2C_Stop (void)
{
	// -------------------------------------------------------------------------------------------
	// Stop the current message transmission by enabling the stop bit in CR1
	// -------------------------------------------------------------------------------------------
	I2C1->CR1 |= (1<<9);  											// Stop I2C
	// -------------------------------------------------------------------------------------------
}

int main(){
	I2C_Config();
	TIM6Config();
	
	uint8_t dec = 0x0;
	uint8_t add = 0x40;
	
	while(1){
		I2C_Start(); // Send the Start Codnition
		I2C_Address (add); // Send the Address
		I2C_Write(dec); // Writing the cmd to LCD using I2C
		dec = (dec+0x1)%256;
		I2C_Stop (); // Genrating Stop Codnition
		Delay_ms(100);
	}
}




